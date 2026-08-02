from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from .models import Service
from .forms import ServiceForm
from business.models import Business


@login_required
def service_list(request):
    business = get_object_or_404(Business, owner=request.user)
    qs = business.services.all()
    from django.core.paginator import Paginator
    paginator = Paginator(qs, 15)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'dashboard/services/list.html', {
        'business': business, 'services': page_obj,
    })


@login_required
def service_create(request):
    business = get_object_or_404(Business, owner=request.user)
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.business = business
            s.save()
            messages.success(request, _('Service added.'))
            return redirect('services:list')
    else:
        form = ServiceForm()
    return render(request, 'dashboard/services/form.html', {
        'form': form, 'business': business, 'action': 'Add',
    })


@login_required
def service_edit(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    service = get_object_or_404(Service, pk=pk, business=business)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, _('Service updated.'))
            return redirect('services:list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'dashboard/services/form.html', {
        'form': form, 'business': business, 'action': 'Edit', 'service': service,
    })


@login_required
def service_delete(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    service = get_object_or_404(Service, pk=pk, business=business)
    if request.method == 'POST':
        service.delete()
        messages.success(request, _('Service deleted.'))
    return redirect('services:list')
