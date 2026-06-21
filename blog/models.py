from django.db import models
from django.conf import settings
from django.utils.text import slugify


class BlogPost(models.Model):
    business = models.ForeignKey(
        'business.Business',
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    content = models.TextField()
    excerpt = models.CharField(max_length=500, blank=True)
    featured_image = models.ImageField(upload_to='blog/featured/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class BlogComment(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"
