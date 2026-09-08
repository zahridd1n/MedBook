from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse, Http404
from django.http import JsonResponse, Http404

from business.models import Business
from services.models import Service
from employees.models import Employee
from appointments.models import Appointment
from appointments.forms import BookingForm
from customers.models import Customer
from notifications.utils import create_notification, build_booking_message
from notifications.tasks import send_telegram_notification_task
from core.seo import get_seo_context, get_json_ld_html


def public_home(request, slug):
    business = get_object_or_404(
        Business.objects.prefetch_related(
            'working_hours',
            'faqs',
        ).only(
            'id', 'name', 'slug', 'about', 'category', 'logo', 'phone', 'email',
            'address', 'city', 'latitude', 'longitude',
            'telegram', 'instagram', 'website',
            'primary_color', 'banner_image', 'button_style', 'card_shadow',
            'navbar_style', 'custom_css', 'is_active',
        ),
        slug=slug, is_active=True,
    )
    seo = get_seo_context(request, business, 'home')
    return render(request, 'public/home.html', {
        'business': business,
        'services': business.services.filter(is_active=True).order_by('order'),
        'employees': business.employees.filter(is_active=True, is_visible_on_public=True).order_by('order'),
        'faqs': business.faqs.filter(is_active=True).order_by('order'),
        'working_hours': business.working_hours.all().order_by('day'),
        'blog_posts': business.blog_posts.filter(is_published=True).order_by('-created_at')[:3],
        'catalog_products': business.products.filter(is_active=True),
        **seo,
        'json_ld_html': get_json_ld_html(seo['json_ld']),
        'seo_enabled': seo['show_advanced_seo'],
    })


def booking_step1_service(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    services = business.services.filter(is_active=True).order_by('order')
    employees = business.employees.filter(is_active=True, is_visible_on_public=True).order_by('order')

    selected_service_id = request.GET.get('service')
    selected_service = None
    if selected_service_id and selected_service_id != '0':
        selected_service = get_object_or_404(Service, pk=selected_service_id, business=business, is_active=True)
        service_employees = employees.filter(services=selected_service)
        if service_employees.exists():
            employees = service_employees

    seo = get_seo_context(request, business, 'booking')
    return render(request, 'public/booking/step1_service.html', {
        'business': business, 'services': services, 'employees': employees,
        'selected_service': selected_service,
        'selected_service_id': selected_service_id or None,
        **seo,
        'json_ld_html': get_json_ld_html(seo['json_ld']),
        'seo_enabled': seo['show_advanced_seo'],
    })


def _get_available_slots(business, employee, duration, date, working_hours_map=None, employee_schedules_map=None):
    """Return list of available time slots (datetime.time) for the given date."""
    day_of_week = date.weekday()
    if working_hours_map is None:
        wh = business.working_hours.filter(day=day_of_week).first()
    else:
        wh = working_hours_map.get(day_of_week)
    if not wh or not wh.is_open or not wh.open_time or not wh.close_time:
        return []

    if employee:
        if employee_schedules_map is None:
            sch = employee.schedules.filter(day=day_of_week).first()
        else:
            sch = employee_schedules_map.get(day_of_week)
        if sch and sch.is_working:
            open_t = sch.start_time or wh.open_time
            close_t = sch.end_time or wh.close_time
        elif sch and not sch.is_working:
            return []
        else:
            open_t, close_t = wh.open_time, wh.close_time
    else:
        open_t, close_t = wh.open_time, wh.close_time

    import datetime as dt

    slots = []
    current = dt.datetime.combine(date, open_t)
    end = dt.datetime.combine(date, close_t)
    step = timedelta(minutes=30)
    duration_delta = timedelta(minutes=duration)

    # Existing confirmed appointments that block slots
    appt_filter = {'business': business, 'date': date, 'status__in': ['new', 'confirmed']}
    if employee:
        appt_filter['employee'] = employee
    existing = list(Appointment.objects.filter(**appt_filter).values_list('time', 'end_time'))

    now = timezone.now()
    if timezone.is_naive(current):
        current = timezone.make_aware(current)
        end = timezone.make_aware(end)

    while current + duration_delta <= end:
        slot_time = current.time()
        slot_end = (current + duration_delta).time()

        # Skip past slots for today
        if date == timezone.localdate() and current <= now:
            current += step
            continue

        conflict = any(
            slot_time < (ae or slot_end) and slot_end > as_
            for as_, ae in existing
        )
        if not conflict:
            slots.append(slot_time)
        current += step

    return slots


DEFAULT_SLOT_DURATION = 30


def booking_step3_datetime(request, slug, service_id=0, employee_id=0):
    business = get_object_or_404(Business, slug=slug, is_active=True)

    service_id = int(service_id)
    employee_id = int(employee_id)

    service = None
    duration = DEFAULT_SLOT_DURATION
    if service_id:
        service = get_object_or_404(Service, pk=service_id, business=business, is_active=True)
        duration = service.duration

    employee = None
    if employee_id:
        employee = get_object_or_404(Employee.objects.prefetch_related('schedules'), pk=employee_id, business=business)

    # Pre-fetch working hours and employee schedules to avoid N+1 queries
    working_hours_map = {wh.day: wh for wh in business.working_hours.all()}
    employee_schedules_map = None
    if employee:
        employee_schedules_map = {s.day: s for s in employee.schedules.all()}

    today = timezone.localdate()
    days = []
    for i in range(14):
        d = today + timedelta(days=i)
        slots = _get_available_slots(
            business, employee, duration, d,
            working_hours_map=working_hours_map,
            employee_schedules_map=employee_schedules_map,
        )
        if slots:
            days.append({'date': d, 'slots': slots})

    import datetime as dt
    selected_date = request.GET.get('date', '')
    selected_slots = []
    if selected_date:
        try:
            d = dt.datetime.strptime(selected_date, '%Y-%m-%d').date()
            selected_slots = _get_available_slots(
                business, employee, duration, d,
                working_hours_map=working_hours_map,
                employee_schedules_map=employee_schedules_map,
            )
        except ValueError:
            pass

    seo = get_seo_context(request, business, 'booking')
    return render(request, 'public/booking/step3_datetime.html', {
        'business': business, 'service': service, 'employee': employee,
        'days': days, 'selected_date': selected_date, 'selected_slots': selected_slots,
        **seo,
        'json_ld_html': get_json_ld_html(seo['json_ld']),
        'seo_enabled': seo['show_advanced_seo'],
    })


def booking_step4_confirm(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)

    service_id = request.GET.get('service') or request.POST.get('service')
    employee_id = request.GET.get('employee') or request.POST.get('employee')
    date_str = request.GET.get('date') or request.POST.get('date')
    time_str = request.GET.get('time') or request.POST.get('time')

    import datetime as dt
    try:
        service = Service.objects.filter(pk=service_id, business=business).first() if service_id else None
        appt_date = dt.datetime.strptime(date_str, '%Y-%m-%d').date()
        appt_time = dt.datetime.strptime(time_str, '%H:%M').time()
        employee = Employee.objects.filter(pk=employee_id, business=business).first() if employee_id else None
    except (ValueError, TypeError):
        return redirect('public-booking-step1', slug=slug)

    if request.method == 'POST':
        if not business.can_create_appointment():
            return render(request, 'public/booking/limit_reached.html', {'business': business})
        form = BookingForm(request.POST)
        if form.is_valid():
            # Get or create customer
            phone = form.cleaned_data['customer_phone']
            name = form.cleaned_data['customer_name']
            customer, _ = Customer.objects.get_or_create(
                business=business, phone=phone, defaults={'full_name': name}
            )
            if customer.full_name != name:
                customer.full_name = name
                customer.save(update_fields=['full_name'])

            # Create appointment
            appt = Appointment.objects.create(
                business=business, customer=customer,
                service=service, employee=employee,
                date=appt_date, time=appt_time,
                notes=form.cleaned_data.get('notes', ''),
                status=Appointment.STATUS_NEW,
            )

            # ── Dashboard notification ────────────────────────────────────
            service_name = service.name if service else '—'
            emp_name = employee.name if employee else ''
            create_notification(
                business=business,
                title='Yangi qabul',
                message=f'{name} — {service_name}{" (" + emp_name + ")" if emp_name else ""}, {appt_date} {appt_time.strftime("%H:%M")}',
                appointment_id=appt.pk,
            )

            # ── Telegram notification (async Celery task) ─────────────────
            if business.telegram_notifications_enabled and business.telegram_chat_id and business.can_use_telegram():
                msg = build_booking_message(appt)
                send_telegram_notification_task.delay(business.telegram_chat_id, msg)

            return redirect('public-booking-success', slug=slug)
    else:
        form = BookingForm(initial={
            'service': service_id, 'employee': employee_id or '',
            'date': date_str, 'time': time_str,
        })

    seo = get_seo_context(request, business, 'booking')
    return render(request, 'public/booking/step4_confirm.html', {
        'business': business, 'service': service, 'employee': employee,
        'date': appt_date, 'time': appt_time, 'form': form,
        **seo,
        'json_ld_html': get_json_ld_html(seo['json_ld']),
        'seo_enabled': seo['show_advanced_seo'],
    })


def public_employee_detail(request, slug, employee_id):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    employee = get_object_or_404(Employee, pk=employee_id, business=business, is_visible_on_public=True)

    total_bookings = Appointment.objects.filter(
        business=business, employee=employee, status__in=['new', 'confirmed', 'completed']
    ).count()

    completed_bookings = Appointment.objects.filter(
        business=business, employee=employee, status='completed'
    ).count()

    completion_pct = int((completed_bookings / total_bookings * 100)) if total_bookings > 0 else 0
    completion_offset = 100 - completion_pct

    seo = get_seo_context(request, business, 'employee', employee=employee)
    return render(request, 'public/employee_detail.html', {
        'business': business,
        'employee': employee,
        'services': employee.services.filter(is_active=True),
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'completion_pct': completion_pct,
        'completion_offset': completion_offset,
        **seo,
        'json_ld_html': get_json_ld_html(seo['json_ld']),
        'seo_enabled': seo['show_advanced_seo'],
    })


def booking_success(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    seo = get_seo_context(request, business, 'booking')
    return render(request, 'public/booking/success.html', {
        'business': business,
        **seo,
        'json_ld_html': get_json_ld_html(seo['json_ld']),
        'seo_enabled': seo['show_advanced_seo'],
    })


def qr_scan_redirect(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)

    from business.models import QRCodeScan
    QRCodeScan.objects.create(
        business=business,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        ip_address=request.META.get('REMOTE_ADDR', None),
        referrer=request.META.get('HTTP_REFERER', '')[:500],
    )

    return redirect('public-home', slug=slug)

def pwa_manifest(request, slug):
    from django.http import HttpResponse
    business = get_object_or_404(Business, slug=slug, is_active=True)

    base_url = request.build_absolute_uri('/')
    start_url = f'/{business.slug}/'

    if business.logo:
        icon_url = request.build_absolute_uri(business.logo.url)
    else:
        icon_url = f'https://ui-avatars.com/api/?name={business.name[:2]}&size=512&background={business.primary_color.lstrip("#") if business.primary_color else "6366f1"}&color=fff&rounded=true'

    manifest = {
        "name": business.name,
        "short_name": business.name[:12],
        "description": f"{business.name} — online bandlov",
        "start_url": start_url,
        "scope": f'/{business.slug}/',
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#ffffff",
        "theme_color": business.primary_color or "#6366f1",
        "lang": "uz",
        "icons": [
            {
                "src": icon_url,
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": icon_url,
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": icon_url,
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable"
            },
        ],
        "shortcuts": [
            {
                "name": "Qabul olish",
                "short_name": "Qabul",
                "description": "Yangi qabul yaratish",
                "url": f'/{business.slug}/book/',
                "icons": [{"src": icon_url, "sizes": "96x96"}]
            }
        ],
        "categories": ["business", "health", "lifestyle"],
    }
    import json
    response = HttpResponse(
        json.dumps(manifest, ensure_ascii=False),
        content_type='application/manifest+json; charset=utf-8'
    )
    response['Cache-Control'] = 'public, max-age=86400'
    return response


def service_worker(request):
    return render(request, 'sw.js', content_type='application/javascript; charset=utf-8')
