from django.contrib import admin
from .models import MarketingVideo


@admin.register(MarketingVideo)
class MarketingVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'duration', 'order', 'is_published', 'youtube_id', 'file_preview')
    list_filter = ('language', 'is_published')
    list_editable = ('order', 'is_published')
    search_fields = ('title', 'description')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'duration', 'order', 'language', 'is_published')
        }),
        ('Video manbai', {
            'fields': ('youtube_id', 'file'),
            'description': 'YouTube ID yoki MP4 fayl yuklang. Agar ikkalasi ham bo\'lmasa, placeholder ko\'rinadi.'
        }),
    )

    def file_preview(self, obj):
        if obj.file and hasattr(obj.file, 'url'):
            return f'<a href="{obj.file.url}" target="_blank">📹 Fayl</a>'
        if obj.youtube_id:
            return f'<a href="https://youtube.com/watch?v={obj.youtube_id}" target="_blank">▶️ YouTube</a>'
        return '—'
    file_preview.allow_tags = True
    file_preview.short_description = 'Manba'
