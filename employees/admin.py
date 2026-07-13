from django.contrib import admin
from .models import Employee, EmployeeSchedule


class EmployeeScheduleInline(admin.TabularInline):
    model = EmployeeSchedule
    extra = 1
    fields = ('day', 'is_working', 'start_time', 'end_time')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'business', 'is_active', 'is_visible_on_public', 'order')
    list_filter = ('is_active', 'is_visible_on_public', 'business')
    search_fields = ('name', 'position', 'business__name')
    readonly_fields = ('created_at',)
    list_editable = ('is_active', 'order')
    inlines = [EmployeeScheduleInline]
    filter_horizontal = ('services',)
    list_select_related = ('business',)


@admin.register(EmployeeSchedule)
class EmployeeScheduleAdmin(admin.ModelAdmin):
    list_display = ('employee', 'get_day_display', 'is_working', 'start_time', 'end_time')
    list_filter = ('is_working', 'day')
    search_fields = ('employee__name', 'employee__business__name')
