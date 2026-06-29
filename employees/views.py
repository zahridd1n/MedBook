from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Employee, EmployeeSchedule
from .forms import EmployeeForm
from business.models import Business


@login_required
def employee_list(request):
    business = get_object_or_404(Business, owner=request.user)
    return render(request, 'dashboard/employees/list.html', {
        'business': business,
        'employees': business.employees.prefetch_related('services').all(),
    })


@login_required
def employee_create(request):
    business = get_object_or_404(Business, owner=request.user)
    if not business.can_add_employee():
        messages.error(
            request,
            f"Xodimlar limiti tugadi ({business.plan_display} — {business.max_employees} ta)."
            f" Yangilash uchun <a href='{''}'>tarifni oshiring</a>."
        )
        return redirect('employees:list')
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, business=business)
        if form.is_valid():
            emp = form.save(commit=False)
            emp.business = business
            emp.save()
            form.save_m2m()
            for day in range(7):
                EmployeeSchedule.objects.get_or_create(
                    employee=emp, day=day,
                    defaults={'is_working': day < 6, 'start_time': '09:00', 'end_time': '18:00'},
                )
            messages.success(request, 'Employee added.')
            return redirect('employees:list')
    else:
        form = EmployeeForm(business=business)
    return render(request, 'dashboard/employees/form.html', {
        'form': form, 'business': business, 'action': 'Add',
    })


@login_required
def employee_edit(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    employee = get_object_or_404(Employee, pk=pk, business=business)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee, business=business)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated.')
            return redirect('employees:list')
    else:
        form = EmployeeForm(instance=employee, business=business)
    return render(request, 'dashboard/employees/form.html', {
        'form': form, 'business': business, 'action': 'Edit', 'employee': employee,
    })


@login_required
def employee_delete(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    employee = get_object_or_404(Employee, pk=pk, business=business)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted.')
    return redirect('employees:list')


@login_required
def employee_schedule(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    employee = get_object_or_404(Employee, pk=pk, business=business)
    existing = {s.day for s in employee.schedules.all()}
    for day in range(7):
        if day not in existing:
            EmployeeSchedule.objects.create(employee=employee, day=day, is_working=False)
    schedules = list(employee.schedules.order_by('day'))

    if request.method == 'POST':
        for sch in schedules:
            sch.is_working = request.POST.get(f'is_working_{sch.day}') == 'on'
            sch.start_time = request.POST.get(f'start_{sch.day}') or None
            sch.end_time = request.POST.get(f'end_{sch.day}') or None
            sch.save()
        messages.success(request, 'Schedule saved.')
        return redirect('employees:list')
    return render(request, 'dashboard/employees/schedule.html', {
        'business': business, 'employee': employee, 'schedules': schedules,
    })
