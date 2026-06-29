from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Appointment
from .forms import AppointmentForm
from business.models import Business
from customers.models import Customer


@login_required
def appointment_list(request):
    business = get_object_or_404(Business, owner=request.user)
    qs = business.appointments.select_related('customer', 'service', 'employee').order_by('-date', '-time')

    status = request.GET.get('status', '')
    search = request.GET.get('q', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(
            Q(customer__full_name__icontains=search) | Q(customer__phone__icontains=search) |
            Q(service__name__icontains=search)
        )
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    return render(request, 'dashboard/appointments/list.html', {
        'business': business, 'appointments': qs,
        'status_choices': Appointment.STATUS_CHOICES, 'selected_status': status,
        'search': search, 'date_from': date_from, 'date_to': date_to,
    })


def _get_or_create_customer(business, name, phone):
    customer, _ = Customer.objects.get_or_create(
        business=business, phone=phone, defaults={'full_name': name}
    )
    if customer.full_name != name:
        customer.full_name = name
        customer.save(update_fields=['full_name'])
    return customer


@login_required
def appointment_create(request):
    business = get_object_or_404(Business, owner=request.user)
    if not business.can_create_appointment():
        messages.error(
            request,
            f"Oylik qabullar limiti tugadi ({business.plan_display} — oyiga 50 ta)."
            f" Yangilash uchun tarifni oshiring."
        )
        return redirect('appointments:list')
    if request.method == 'POST':
        form = AppointmentForm(request.POST, business=business)
        if form.is_valid():
            customer = _get_or_create_customer(
                business, form.cleaned_data['customer_name'], form.cleaned_data['customer_phone']
            )
            appt = form.save(commit=False)
            appt.business = business
            appt.customer = customer
            appt.save()
            messages.success(request, 'Appointment created.')
            return redirect('appointments:list')
    else:
        form = AppointmentForm(business=business)
    return render(request, 'dashboard/appointments/form.html', {
        'form': form, 'business': business, 'action': 'Create',
    })


@login_required
def appointment_edit(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    appt = get_object_or_404(Appointment, pk=pk, business=business)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appt, business=business)
        if form.is_valid():
            customer = _get_or_create_customer(
                business, form.cleaned_data['customer_name'], form.cleaned_data['customer_phone']
            )
            appt = form.save(commit=False)
            appt.customer = customer
            appt.save()
            messages.success(request, 'Appointment updated.')
            return redirect('appointments:list')
    else:
        form = AppointmentForm(instance=appt, business=business)
    return render(request, 'dashboard/appointments/form.html', {
        'form': form, 'business': business, 'action': 'Edit', 'appointment': appt,
    })


@login_required
def appointment_delete(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    appt = get_object_or_404(Appointment, pk=pk, business=business)
    if request.method == 'POST':
        appt.delete()
        messages.success(request, 'Appointment deleted.')
    return redirect('appointments:list')


@login_required
def appointment_status(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    appt = get_object_or_404(Appointment, pk=pk, business=business)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Appointment.STATUS_CHOICES):
            appt.status = new_status
            appt.save(update_fields=['status'])
            messages.success(request, f'Status: {appt.get_status_display()}')
    return redirect('appointments:list')
