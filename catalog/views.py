import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from business.models import Business
from .models import Product, Order
from .forms import ProductForm, OrderStatusForm

logger = logging.getLogger(__name__)


# ─── Dashboard: Products ───────────────────────────────────────────────────────

@login_required
def product_list(request):
    business = get_object_or_404(Business, owner=request.user)
    products = business.products.all()
    return render(request, 'dashboard/catalog/product_list.html', {
        'business': business,
        'products': products,
        'active_count': products.filter(is_active=True).count(),
    })


@login_required
def product_add(request):
    business = get_object_or_404(Business, owner=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.business = business
            product.save()
            messages.success(request, f'✅ "{product.name}" mahsulot qo\'shildi.')
            return redirect('catalog:product_list')
    else:
        form = ProductForm()
    return render(request, 'dashboard/catalog/product_form.html', {
        'business': business,
        'form': form,
        'title': 'Yangi mahsulot',
        'action': 'Qo\'shish',
    })


@login_required
def product_edit(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    product = get_object_or_404(Product, pk=pk, business=business)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ "{product.name}" yangilandi.')
            return redirect('catalog:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'dashboard/catalog/product_form.html', {
        'business': business,
        'form': form,
        'product': product,
        'title': f'Tahrirlash: {product.name}',
        'action': 'Saqlash',
    })


@login_required
@require_POST
def product_delete(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    product = get_object_or_404(Product, pk=pk, business=business)
    name = product.name
    # Delete image file
    if product.image:
        try:
            product.image.delete(save=False)
        except Exception:
            pass
    product.delete()
    messages.success(request, f'🗑️ "{name}" o\'chirildi.')
    return redirect('catalog:product_list')


@login_required
@require_POST
def product_toggle(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    product = get_object_or_404(Product, pk=pk, business=business)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])
    return JsonResponse({'ok': True, 'is_active': product.is_active})


# ─── Dashboard: Orders ────────────────────────────────────────────────────────

@login_required
def order_list(request):
    business = get_object_or_404(Business, owner=request.user)
    status_filter = request.GET.get('status', '')
    orders = business.orders.select_related('product').all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'dashboard/catalog/order_list.html', {
        'business': business,
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
        'counts': {
            'all': business.orders.count(),
            'new': business.orders.filter(status=Order.STATUS_NEW).count(),
            'confirmed': business.orders.filter(status=Order.STATUS_CONFIRMED).count(),
            'completed': business.orders.filter(status=Order.STATUS_COMPLETED).count(),
            'cancelled': business.orders.filter(status=Order.STATUS_CANCELLED).count(),
        },
    })


@login_required
@require_POST
def order_update_status(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    order = get_object_or_404(Order, pk=pk, business=business)
    new_status = request.POST.get('status')
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save(update_fields=['status'])
        return JsonResponse({'ok': True, 'status': new_status, 'label': order.get_status_display()})
    return JsonResponse({'ok': False}, status=400)


@login_required
@require_POST
def order_delete(request, pk):
    business = get_object_or_404(Business, owner=request.user)
    order = get_object_or_404(Order, pk=pk, business=business)
    order.delete()
    messages.success(request, '🗑️ Buyurtma o\'chirildi.')
    return redirect('catalog:order_list')


# ─── Public: Catalog Page ─────────────────────────────────────────────────────

def public_catalog(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    products = business.products.filter(is_active=True).order_by('order', 'name')
    return render(request, 'public/catalog/catalog.html', {
        'business': business,
        'products': products,
    })


# ─── Public: Submit Order (AJAX) ──────────────────────────────────────────────

@require_POST
def public_order_submit(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)

    customer_name = request.POST.get('customer_name', '').strip()
    customer_phone = request.POST.get('customer_phone', '').strip()
    product_id = request.POST.get('product_id', '').strip()
    notes = request.POST.get('notes', '').strip()

    if not customer_name or not customer_phone:
        return JsonResponse({'ok': False, 'error': 'Ism va telefon raqam majburiy.'}, status=400)

    product = None
    if product_id:
        try:
            product = Product.objects.get(pk=product_id, business=business, is_active=True)
        except Product.DoesNotExist:
            pass

    order = Order.objects.create(
        business=business,
        product=product,
        customer_name=customer_name,
        customer_phone=customer_phone,
        notes=notes,
        status=Order.STATUS_NEW,
    )

    # ── Dashboard notification ────────────────────────────────────────────────
    try:
        from notifications.utils import create_notification
        product_name = product.name if product else 'Umumiy so\'rov'
        create_notification(
            business=business,
            title='Yangi buyurtma 🛒',
            message=f'{customer_name} — {product_name} ({customer_phone})',
            notification_type='booking',
        )
    except Exception as e:
        logger.error(f'[Order] Dashboard notification failed: {e}')

    # ── Telegram notification (only if connected) ─────────────────────────────
    try:
        if business.telegram_notifications_enabled and business.telegram_chat_id:
            from notifications.tasks import send_telegram_notification_task
            product_name = product.name if product else 'Umumiy so\'rov'
            msg = (
                f'🛒 <b>Yangi buyurtma!</b>\n'
                f'━━━━━━━━━━━━━━━\n'
                f'📦 <b>Mahsulot:</b> {product_name}\n'
                f'👤 <b>Mijoz:</b> {customer_name}\n'
                f'📞 <b>Telefon:</b> {customer_phone}\n'
            )
            if notes:
                msg += f'📝 <b>Izoh:</b> {notes}\n'
            msg += f'━━━━━━━━━━━━━━━\n<i>Dashboard\'dan boshqaring</i>'
            send_telegram_notification_task.delay(business.telegram_chat_id, msg)
    except Exception as e:
        logger.error(f'[Order] Telegram notification failed: {e}')

    return JsonResponse({
        'ok': True,
        'message': f'✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog\'lanamiz.',
    })
