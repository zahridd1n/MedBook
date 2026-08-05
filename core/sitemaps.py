from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from business.models import Business
from blog.models import BlogPost
from employees.models import Employee


class MarketingSitemap(Sitemap):
    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        return ['marketing:home', 'marketing:pricing', 'marketing:faq', 'marketing:contact', 'marketing:businesses', 'marketing:tutorials']

    def location(self, item):
        return reverse(item)


class BusinessSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Business.objects.filter(is_active=True).order_by('id').only('slug', 'updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('public-home', args=[obj.slug])


class BlogSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return BlogPost.objects.filter(is_published=True).order_by('-created_at').select_related('business').only('slug', 'business__slug', 'updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('public-blog-detail', args=[obj.business.slug, obj.slug])


class EmployeeSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return Employee.objects.filter(is_active=True, is_visible_on_public=True).order_by('id').select_related('business').only('id', 'business__slug')

    def location(self, obj):
        return reverse('public-employee-detail', args=[obj.business.slug, obj.id])


sitemaps = {
    'marketing': MarketingSitemap,
    'businesses': BusinessSitemap,
    'blog': BlogSitemap,
    'employees': EmployeeSitemap,
}
