from django.contrib import admin
from .models import BlogPost, BlogComment


class BlogCommentInline(admin.TabularInline):
    model = BlogComment
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('name', 'email', 'content', 'is_approved', 'created_at')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'is_published', 'views_count', 'created_at')
    list_filter = ('is_published', 'business', 'created_at')
    search_fields = ('title', 'content', 'business__name')
    readonly_fields = ('slug', 'views_count', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [BlogCommentInline]
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('business', 'title', 'slug', 'excerpt')
        }),
        ('Mazmuni', {
            'fields': ('content', 'featured_image')
        }),
        ('Nashr', {
            'fields': ('is_published', 'views_count')
        }),
        ('Vaqtlar', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(business__owner=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        if not change:
            obj.business = request.user.business
        super().save_model(request, obj, form, change)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'post', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'email', 'content', 'post__title')
    readonly_fields = ('created_at',)
    actions = ['approve_comments', 'reject_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "Izohlar tasdiqlandi.")

    def reject_comments(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, "Izohlar rad etildi.")

    approve_comments.short_description = "Tanlangan izohlarni tasdiqlash"
    reject_comments.short_description = "Tanlangan izohlarni rad etish"
