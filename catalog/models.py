from django.db import models
from business.models import Business


def product_image_upload_path(instance, filename):
    return f'catalog/{instance.business.slug}/{filename}'


class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200, verbose_name='Nomi')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Narx')
    price_label = models.CharField(
        max_length=50, blank=True,
        verbose_name='Narx belgisi',
        help_text='Masalan: "so\'m", "USD", "Narx so\'rovga qarab"',
        default='so\'m'
    )
    image = models.ImageField(upload_to=product_image_upload_path, verbose_name='Rasm')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    order = models.PositiveIntegerField(default=0, verbose_name='Tartib')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Mahsulot'
        verbose_name_plural = 'Mahsulotlar'
        indexes = [
            models.Index(fields=['business', 'is_active']),
            models.Index(fields=['business', 'order']),
        ]

    def __str__(self):
        return f'{self.name} ({self.business.name})'

    @property
    def price_display(self):
        if self.price_label:
            return f'{self.price:,.0f} {self.price_label}'
        return f'{self.price:,.0f}'


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Yangi'),
        (STATUS_CONFIRMED, 'Tasdiqlangan'),
        (STATUS_COMPLETED, 'Yakunlangan'),
        (STATUS_CANCELLED, 'Bekor qilingan'),
    ]
    STATUS_COLORS = {
        STATUS_NEW: 'primary',
        STATUS_CONFIRMED: 'success',
        STATUS_COMPLETED: 'secondary',
        STATUS_CANCELLED: 'danger',
    }

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', verbose_name='Mahsulot'
    )
    customer_name = models.CharField(max_length=200, verbose_name='Mijoz ismi')
    customer_phone = models.CharField(max_length=30, verbose_name='Telefon raqam')
    notes = models.TextField(blank=True, verbose_name='Izoh')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default=STATUS_NEW, verbose_name='Holat'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'
        indexes = [
            models.Index(fields=['business', 'status']),
            models.Index(fields=['business', 'created_at']),
        ]

    def __str__(self):
        product_name = self.product.name if self.product else 'Umumiy'
        return f'{self.customer_name} — {product_name}'

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')
