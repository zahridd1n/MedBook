from datetime import timedelta
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.options import IS_POPUP_VAR
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from .models import SiteSettings, PricingPlan, PricingPlanFeature, BusinessSubscription


class PricingPlanFeatureInline(admin.TabularInline):
    model = PricingPlanFeature
    extra = 1
    fields = ('text', 'is_included', 'order')


# ─── Custom Filter: Muddati yaqin ───────────────────────────────────────────
class ExpiringSoonFilter(SimpleListFilter):
    title = "Muddati yaqin"
    parameter_name = 'expiring_soon'

    def lookups(self, request, model_admin):
        return [
            ('7', '7 kun ichida'),
            ('14', '14 kun ichida'),
            ('30', '30 kun ichida'),
            ('expired', 'Muddati o\'tgan'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        value = self.value()
        if value == '7':
            return queryset.filter(
                subscription_end__gte=now,
                subscription_end__lte=now + timedelta(days=7),
                subscription_status__in=['trial', 'active'],
            )
        if value == '14':
            return queryset.filter(
                subscription_end__gte=now,
                subscription_end__lte=now + timedelta(days=14),
                subscription_status__in=['trial', 'active'],
            )
        if value == '30':
            return queryset.filter(
                subscription_end__gte=now,
                subscription_end__lte=now + timedelta(days=30),
                subscription_status__in=['trial', 'active'],
            )
        if value == 'expired':
            return queryset.filter(subscription_status='expired')
        return queryset


# ─── Custom Filter: Tarif bo'yicha ─────────────────────────────────────────
class PlanFilter(SimpleListFilter):
    title = "Tarif"
    parameter_name = 'plan'

    def lookups(self, request, model_admin):
        return [
            ('free', 'Start'),
            ('growth', 'Pro'),
            ('enterprise', 'Max'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(subscription_plan=self.value())
        return queryset


# ─── Custom Filter: Obuna holati bo'yicha ──────────────────────────────────
class SubscriptionStatusFilter(SimpleListFilter):
    title = "Obuna holati"
    parameter_name = 'sub_status'

    def lookups(self, request, model_admin):
        return [
            ('trial', 'Sinov'),
            ('active', 'Faol'),
            ('expired', 'Muddati o\'tgan'),
            ('cancelled', 'Bekor qilingan'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(subscription_status=self.value())
        return queryset


# ─── Inline: to'lovlar tarixi ──────────────────────────────────────────────
class SubscriptionPaymentInline(admin.TabularInline):
    model = None  # Will be set dynamically
    extra = 0
    readonly_fields = ('plan', 'amount', 'receipt', 'status', 'note', 'created_at')
    can_delete = False
    max_num = 0
    verbose_name = "To'lov"
    verbose_name_plural = "To'lovlar tarixi"


# ─── Asosiy Admin ──────────────────────────────────────────────────────────
@admin.register(BusinessSubscription)
class BusinessSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'business_name', 'owner_info', 'subscription_plan_colored',
        'subscription_status_colored', 'subscription_dates',
        'days_remaining', 'is_active_badge', 'is_blocked_badge',
    )
    list_filter = (
        PlanFilter, SubscriptionStatusFilter, ExpiringSoonFilter,
        'is_active', 'is_blocked',
    )
    search_fields = (
        'name', 'slug', 'owner__email', 'owner__first_name',
        'owner__last_name', 'phone',
    )
    list_select_related = ('owner',)
    list_per_page = 25
    change_list_template = 'admin/superadmin/businesssubscription/change_list.html'
    change_form_template = 'admin/superadmin/businesssubscription/change_form.html'

    fieldsets = (
        ('Biznes', {
            'fields': ('name', 'slug', 'owner', 'category', 'phone', 'email'),
        }),
        ('Obuna', {
            'fields': (
                'subscription_plan', 'subscription_status',
                'subscription_start', 'subscription_end',
            ),
        }),
        ('Holat', {
            'fields': ('is_active', 'is_blocked'),
        }),
    )
    readonly_fields = ('name', 'slug', 'owner', 'category', 'phone', 'email')

    # ─── List dagi ustunlar ──────────────────────────────────────────────
    @admin.display(description='Biznes', ordering='name')
    def business_name(self, obj):
        url = reverse('admin:business_business_change', args=[obj.pk])
        return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.name)

    @admin.display(description='Egasi', ordering='owner__email')
    def owner_info(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.owner_id])
        return format_html(
            '<a href="{}">{}</a>',
            url, obj.owner.email or '—'
        )

    @admin.display(description='Tarif', ordering='subscription_plan')
    def subscription_plan_colored(self, obj):
        colors = {'free': '#6b7280', 'growth': '#6366f1', 'enterprise': '#f59e0b'}
        labels = {'free': 'Start', 'growth': 'Pro', 'enterprise': 'Max'}
        color = colors.get(obj.subscription_plan, '#6b7280')
        return format_html(
            '<span style="color:{};font-weight:600">● {}</span>',
            color, labels.get(obj.subscription_plan, obj.subscription_plan)
        )

    @admin.display(description='Holati', ordering='subscription_status')
    def subscription_status_colored(self, obj):
        colors = {
            'trial': '#3b82f6', 'active': '#10b981',
            'expired': '#ef4444', 'cancelled': '#6b7280',
        }
        labels = {
            'trial': 'Sinov', 'active': 'Faol',
            'expired': 'Muddati o\'tgan', 'cancelled': 'Bekor qilingan',
        }
        color = colors.get(obj.subscription_status, '#6b7280')
        label = labels.get(obj.subscription_status, obj.subscription_status)
        return format_html(
            '<span style="color:{};font-weight:600">● {}</span>',
            color, label
        )

    @admin.display(description='Obuna muddati')
    def subscription_dates(self, obj):
        if not obj.subscription_start and not obj.subscription_end:
            return '—'
        start = obj.subscription_start.strftime('%d.%m.%Y') if obj.subscription_start else '?'
        end = obj.subscription_end.strftime('%d.%m.%Y') if obj.subscription_end else '?'
        return format_html('{} → <strong>{}</strong>', start, end)

    @admin.display(description='Qolgan kun')
    def days_remaining(self, obj):
        if not obj.subscription_end:
            return format_html('<span style="color:#6b7280">—</span>')
        remaining = (obj.subscription_end - timezone.now()).days
        if remaining < 0:
            return format_html('<span style="color:#ef4444;font-weight:600">⚠ {}</span>', 'Muddati o\'tgan')
        if remaining <= 7:
            return format_html('<span style="color:#f59e0b;font-weight:600">{}</span>', f'{remaining} kun')
        if remaining <= 30:
            return format_html('<span style="color:#3b82f6">{}</span>', f'{remaining} kun')
        return format_html('<span style="color:#10b981">{}</span>', f'{remaining} kun')

    @admin.display(description='Aktiv', boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active

    @admin.display(description='Blok', boolean=True)
    def is_blocked_badge(self, obj):
        return obj.is_blocked

    # ─── Amallar ─────────────────────────────────────────────────────────
    actions = [
        'set_plan_free', 'set_plan_growth', 'set_plan_enterprise',
        'activate_subscription', 'expire_subscription',
        'extend_7_days', 'extend_30_days',
        'block_selected', 'unblock_selected',
    ]

    @admin.action(description="➜ Start (free) tarifiga o'tkazish")
    def set_plan_free(self, request, queryset):
        updated = queryset.update(subscription_plan='free')
        self.message_user(request, f"{updated} ta biznes Start tarifiga o'tkazildi.")

    @admin.action(description="➜ Pro (growth) tarifiga o'tkazish")
    def set_plan_growth(self, request, queryset):
        updated = queryset.update(subscription_plan='growth',
                                  subscription_status='active',
                                  subscription_start=timezone.now())
        self.message_user(request, f"{updated} ta biznes Pro tarifiga o'tkazildi.")

    @admin.action(description="➜ Max (enterprise) tarifiga o'tkazish")
    def set_plan_enterprise(self, request, queryset):
        updated = queryset.update(subscription_plan='enterprise',
                                  subscription_status='active',
                                  subscription_start=timezone.now())
        self.message_user(request, f"{updated} ta biznes Max tarifiga o'tkazildi.")

    @admin.action(description="✅ Obunani faollashtirish")
    def activate_subscription(self, request, queryset):
        updated = queryset.update(subscription_status='active',
                                  subscription_start=timezone.now())
        self.message_user(request, f"{updated} ta obuna faollashtirildi.")

    @admin.action(description="❌ Obunani muddatini tugatish")
    def expire_subscription(self, request, queryset):
        updated = queryset.update(subscription_status='expired',
                                  subscription_end=timezone.now())
        self.message_user(request, f"{updated} ta obuna muddati tugatildi.")

    @admin.action(description="+7 kun obunani uzaytirish")
    def extend_7_days(self, request, queryset):
        now = timezone.now()
        for obj in queryset:
            current_end = obj.subscription_end or now
            new_end = max(current_end, now) + timedelta(days=7)
            BusinessSubscription.objects.filter(pk=obj.pk).update(
                subscription_end=new_end,
                subscription_status='active',
            )
        self.message_user(request, f"{queryset.count()} ta obuna 7 kunga uzaytirildi.")

    @admin.action(description="+30 kun obunani uzaytirish")
    def extend_30_days(self, request, queryset):
        now = timezone.now()
        for obj in queryset:
            current_end = obj.subscription_end or now
            new_end = max(current_end, now) + timedelta(days=30)
            BusinessSubscription.objects.filter(pk=obj.pk).update(
                subscription_end=new_end,
                subscription_status='active',
            )
        self.message_user(request, f"{queryset.count()} ta obuna 30 kunga uzaytirildi.")

    @admin.action(description="⛔ Bizneslarni bloklash")
    def block_selected(self, request, queryset):
        updated = queryset.update(is_blocked=True)
        self.message_user(request, f"{updated} ta biznes bloklandi.")

    @admin.action(description="🔓 Bizneslarni blokdan chiqarish")
    def unblock_selected(self, request, queryset):
        updated = queryset.update(is_blocked=False)
        self.message_user(request, f"{updated} ta biznes blokdan chiqarildi.")

    # ─── Change form ─────────────────────────────────────────────────────
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['subscription_plan'].label = "Tarif"
            form.base_fields['subscription_status'].label = "Holat"
            form.base_fields['subscription_start'].label = "Boshlanish vaqti"
            form.base_fields['subscription_end'].label = "Tugash vaqti"
            form.base_fields['is_active'].label = "Aktiv"
            form.base_fields['is_blocked'].label = "Bloklangan"
        return form

    # ─── Changelist view with stats ──────────────────────────────────────
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        now = timezone.now()
        qs = BusinessSubscription.objects.all()

        extra_context['stats'] = {
            'total': qs.count(),
            'by_plan': {
                'free': qs.filter(subscription_plan='free').count(),
                'growth': qs.filter(subscription_plan='growth').count(),
                'enterprise': qs.filter(subscription_plan='enterprise').count(),
            },
            'by_status': {
                'trial': qs.filter(subscription_status='trial').count(),
                'active': qs.filter(subscription_status='active').count(),
                'expired': qs.filter(subscription_status='expired').count(),
                'cancelled': qs.filter(subscription_status='cancelled').count(),
            },
            'blocked': qs.filter(is_blocked=True).count(),
            'expiring_7': qs.filter(
                subscription_end__gte=now,
                subscription_end__lte=now + timedelta(days=7),
                subscription_status__in=['trial', 'active'],
            ).count(),
            'expiring_30': qs.filter(
                subscription_end__gte=now,
                subscription_end__lte=now + timedelta(days=30),
                subscription_status__in=['trial', 'active'],
            ).count(),
        }

        return super().changelist_view(request, extra_context)

    # ─── Permissionlar ───────────────────────────────────────────────────
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ─── Eski admin registratsiyalari ─────────────────────────────────────────
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('hero_title', 'contact_phone', 'contact_email', 'updated_at')
    fieldsets = (
        ('Marketing', {
            'fields': ('hero_title', 'hero_subtitle', 'marketing_content', 'logo', 'logo_light', 'favicon')
        }),
        ('Narxlar', {
            'fields': (
                'starter_price', 'growth_price_monthly', 'growth_price_yearly',
                'enterprise_price_monthly', 'enterprise_price_yearly'
            ),
        }),
        ('Statistika', {
            'fields': ('stats_uptime', 'stats_appointments', 'stats_businesses'),
        }),
        ('Aloqa', {
            'fields': ('contact_phone', 'contact_email', 'contact_telegram'),
        }),
        ("To'lov", {
            'fields': ('payment_card_number', 'payment_card_holder'),
        }),
        ('SEO', {
            'fields': ('default_meta_description', 'default_og_image', 'google_site_verification', 'yandex_verification'),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price_monthly', 'price_yearly', 'is_active', 'is_popular', 'order')
    list_filter = ('is_active', 'is_popular')
    search_fields = ('name', 'slug', 'description')
    list_editable = ('is_active', 'is_popular', 'order')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PricingPlanFeatureInline]
    fieldsets = (
        ('Asosiy', {
            'fields': ('name', 'slug', 'description', 'order')
        }),
        ('Narxlar', {
            'fields': ('price_monthly', 'discount_3months', 'discount_yearly', 'yearly_badge'),
            'description': (
                'price_monthly = asosiy oylik narx (UZS) | '
                'discount_3months = 3 oylik chegirma % | '
                'discount_yearly = yillik chegirma % | '
                'yearly_badge = badge (bo\'sh qolsa avtomatik)'
            ),
        }),
        ('Cheklovlar', {
            'fields': ('max_employees', 'max_appointments_monthly'),
        }),
        ('Imkoniyatlar', {
            'fields': (
                'allow_telegram', 'allow_email', 'allow_custom_domain',
                'allow_branding', 'allow_custom_css', 'allow_google_calendar',
                'allow_api', 'allow_white_label'
            ),
        }),
        ('Holat', {
            'fields': ('is_active', 'is_popular'),
        }),
    )


@admin.register(PricingPlanFeature)
class PricingPlanFeatureAdmin(admin.ModelAdmin):
    list_display = ('text', 'plan', 'is_included', 'order')
    list_filter = ('is_included', 'plan')
    search_fields = ('text', 'plan__name')
    list_editable = ('is_included', 'order')
