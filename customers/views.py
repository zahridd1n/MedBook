from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, OuterRef, Subquery, Sum
from django.utils.translation import gettext as _
from .models import Customer
from business.models import Business
from appointments.models import Appointment


@login_required
def customer_list(request):
    business = get_object_or_404(Business, owner=request.user)
    qs = business.customers.annotate(
        appt_count=Count('appointments'),
        last_visit_date=Subquery(
            Appointment.objects.filter(
                customer=OuterRef('pk'), status='completed'
            ).order_by('-date').values('date')[:1]
        ),
    )
    search = request.GET.get('q', '')
    if search:
        qs = qs.filter(Q(full_name__icontains=search) | Q(phone__icontains=search))

    total_customers = business.customers.count()
    total_appts_all = Appointment.objects.filter(business=business).count()

    return render(request, 'dashboard/customers/list.html', {
        'business': business, 'customers_data': qs, 'search': search,
        'total_customers': total_customers,
        'total_appts_all': total_appts_all,
    })


from appointments.forms import AppointmentForm


@login_required
def customer_detail(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    customer = get_object_or_404(Customer, pk=pk, business=business)
    appointments = customer.appointments.select_related('service', 'employee').order_by('-date', '-time')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_note':
            note_text = request.POST.get('customer_notes', '').strip()
            if note_text:
                customer.notes = (customer.notes + '\n---\n' + note_text) if customer.notes else note_text
                customer.save(update_fields=['notes'])
                messages.success(request, _('Eslatma qo\'shildi.'))
        elif action == 'add_appointment':
            form = AppointmentForm(request.POST, business=business)
            if form.is_valid():
                from appointments.views import _get_or_create_customer
                cust = _get_or_create_customer(business, customer.full_name, customer.phone)
                appt = form.save(commit=False)
                appt.business = business
                appt.customer = cust
                appt.save()
                messages.success(request, _('Yangi qabul qo\'shildi.'))
        return redirect('customers:detail', pk=pk)

    total_spent = sum(
        (a.service.price for a in appointments.filter(service__isnull=False) if a.service),
        0
    )
    completed_count = appointments.filter(status='completed').count()

    return render(request, 'dashboard/customers/detail.html', {
        'business': business,
        'customer': customer,
        'appointments': appointments,
        'total_spent': total_spent,
        'completed_count': completed_count,
        'appointment_form': AppointmentForm(business=business),
    })
