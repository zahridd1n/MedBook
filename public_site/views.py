from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from business.models import Business
from services.models import Service
from employees.models import Employee
from appointments.models import Appointment
from appointments.forms import BookingForm
from customers.models import Customer
from notifications.utils import create_notification, build_booking_message
from notifications.tasks import send_telegram_notification_task


def public_home(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    return render(request, 'public/home.html', {
        'business': business,
        'services': business.services.filter(is_active=True).order_by('order'),
        'employees': business.employees.filter(is_active=True).order_by('order'),
        'faqs': business.faqs.filter(is_active=True).order_by('order'),
        'working_hours': business.working_hours.all().order_by('day'),
        'blog_posts': business.blog_posts.filter(is_published=True).order_by('-created_at')[:3],
    })


def booking_step1_service(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    services = business.services.filter(is_active=True).order_by('order')
    employees = business.employees.filter(is_active=True).order_by('order')

    selected_service_id = request.GET.get('service')
    selected_service = None
    if selected_service_id and selected_service_id != '0':
        selected_service = get_object_or_404(Service, pk=selected_service_id, business=business, is_active=True)
        service_employees = employees.filter(services=selected_service)
        if service_employees.exists():
            employees = service_employees

    return render(request, 'public/booking/step1_service.html', {
        'business': business, 'services': services, 'employees': employees,
        'selected_service': selected_service,
        'selected_service_id': selected_service_id or None,
    })


def _get_available_slots(business, employee, duration, date):
    """Return list of available time slots (datetime.time) for the given date."""
    day_of_week = date.weekday()
    try:
        wh = business.working_hours.get(day=day_of_week)
        if not wh.is_open or not wh.open_time or not wh.close_time:
            return []
    except Exception:
        return []

    if employee:
        try:
            sch = employee.schedules.get(day=day_of_week)
            if not sch.is_working:
                return []
            open_t = sch.start_time or wh.open_time
            close_t = sch.end_time or wh.close_time
        except Exception:
            open_t, close_t = wh.open_time, wh.close_time
    else:
        open_t, close_t = wh.open_time, wh.close_time

    slots = []
    current = datetime.combine(date, open_t)
    end = datetime.combine(date, close_t)
    step = timedelta(minutes=30)
    duration_delta = timedelta(minutes=duration)

    # Existing confirmed appointments that block slots
    appt_filter = {'business': business, 'date': date, 'status__in': ['new', 'confirmed']}
    if employee:
        appt_filter['employee'] = employee
    existing = list(Appointment.objects.filter(**appt_filter).values_list('time', 'end_time'))

    now = datetime.now()

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
        employee = get_object_or_404(Employee, pk=employee_id, business=business)

    today = timezone.localdate()
    days = []
    for i in range(14):
        d = today + timedelta(days=i)
        slots = _get_available_slots(business, employee, duration, d)
        if slots:
            days.append({'date': d, 'slots': slots})

    selected_date = request.GET.get('date', '')
    selected_slots = []
    if selected_date:
        try:
            d = datetime.strptime(selected_date, '%Y-%m-%d').date()
            selected_slots = _get_available_slots(business, employee, duration, d)
        except ValueError:
            pass

    return render(request, 'public/booking/step3_datetime.html', {
        'business': business, 'service': service, 'employee': employee,
        'days': days, 'selected_date': selected_date, 'selected_slots': selected_slots,
    })


def booking_step4_confirm(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)

    service_id = request.GET.get('service') or request.POST.get('service')
    employee_id = request.GET.get('employee') or request.POST.get('employee')
    date_str = request.GET.get('date') or request.POST.get('date')
    time_str = request.GET.get('time') or request.POST.get('time')

    try:
        service = Service.objects.filter(pk=service_id, business=business).first() if service_id else None
        appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appt_time = datetime.strptime(time_str, '%H:%M').time()
        employee = Employee.objects.filter(pk=employee_id, business=business).first() if employee_id else None
    except Exception:
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
            service_name = service.name if service else 'No service'
            create_notification(
                business=business,
                title='New Booking',
                message=f'{name} booked {service_name} on {appt_date} at {appt_time.strftime("%H:%M")}',
                appointment_id=appt.pk,
            )

            # ── Telegram notification (async Celery task) ─────────────────
            if business.telegram_notifications_enabled and business.telegram_chat_id:
                msg = build_booking_message(appt)
                send_telegram_notification_task.delay(business.telegram_chat_id, msg)

            return redirect('public-booking-success', slug=slug)
    else:
        form = BookingForm(initial={
            'service': service_id, 'employee': employee_id or '',
            'date': date_str, 'time': time_str,
        })

    return render(request, 'public/booking/step4_confirm.html', {
        'business': business, 'service': service, 'employee': employee,
        'date': appt_date, 'time': appt_time, 'form': form,
    })


def booking_success(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    return render(request, 'public/booking/success.html', {'business': business})
