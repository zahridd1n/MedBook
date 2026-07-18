from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from core.tasks import invalidate_business_seo_cache


@receiver(post_save, sender='business.Business')
def business_saved(sender, instance, **kwargs):
    transaction.on_commit(lambda: invalidate_business_seo_cache.delay(instance.id))


@receiver(post_delete, sender='business.Business')
def business_deleted(sender, instance, **kwargs):
    from core.seo import invalidate_seo_cache
    invalidate_seo_cache(instance.id)


@receiver(post_save, sender='blog.BlogPost')
def blog_post_saved(sender, instance, **kwargs):
    if instance.business_id:
        transaction.on_commit(lambda: invalidate_business_seo_cache.delay(instance.business_id))


@receiver(post_delete, sender='blog.BlogPost')
def blog_post_deleted(sender, instance, **kwargs):
    if instance.business_id:
        from core.seo import invalidate_seo_cache
        invalidate_seo_cache(instance.business_id)


@receiver(post_save, sender='employees.Employee')
def employee_saved(sender, instance, **kwargs):
    if instance.business_id:
        transaction.on_commit(lambda: invalidate_business_seo_cache.delay(instance.business_id))


@receiver(post_save, sender='business.FAQ')
def faq_saved(sender, instance, **kwargs):
    if instance.business_id:
        transaction.on_commit(lambda: invalidate_business_seo_cache.delay(instance.business_id))


@receiver(post_save, sender='business.WorkingHours')
def working_hours_saved(sender, instance, **kwargs):
    if instance.business_id:
        transaction.on_commit(lambda: invalidate_business_seo_cache.delay(instance.business_id))
