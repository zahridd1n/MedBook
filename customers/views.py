from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Customer
from business.models import Business


@login_required
def customer_list(request):
    business = get_object_or_404(Business, owner=request.user)
    qs = business.customers.all()
    search = request.GET.get('q', '')
    if search:
        qs = qs.filter(Q(full_name__icontains=search) | Q(phone__icontains=search))
    data = [{'customer': c, 'appointment_count': c.appointment_count, 'last_visit': c.last_visit} for c in qs]
    return render(request, 'dashboard/customers/list.html', {
        'business': business, 'customers_data': data, 'search': search,
    })


@login_required
def customer_detail(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    customer = get_object_or_404(Customer, pk=pk, business=business)
    appointments = customer.appointments.select_related('service', 'employee').order_by('-date', '-time')
    return render(request, 'dashboard/customers/detail.html', {
        'business': business, 'customer': customer, 'appointments': appointments,
    })
