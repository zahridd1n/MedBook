from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import BlogPost, BlogComment
from .forms import BlogPostForm, BlogCommentForm


# ─── Dashboard Views ──────────────────────────────────────────────────────

@login_required
@require_http_methods(["GET"])
def blog_list(request):
    """Biznes uchun blog postlarni ko'rsatish"""
    try:
        business = request.user.business
    except:
        return redirect('dashboard:home')
    
    posts = business.blog_posts.all()
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'posts': posts,
        'active_tab': 'blog',
    }
    return render(request, 'dashboard/blog/list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def blog_create(request):
    """Yangi blog post yaratish"""
    try:
        business = request.user.business
    except:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.business = business
            post.save()
            return redirect('blog:list')
    else:
        form = BlogPostForm()
    
    context = {
        'form': form,
        'active_tab': 'blog',
        'title': 'Yangi Blog Qo\'shish'
    }
    return render(request, 'dashboard/blog/form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def blog_edit(request, pk):
    """Blog post'ni tahrirlash"""
    try:
        business = request.user.business
    except:
        return redirect('dashboard:home')
    
    post = get_object_or_404(BlogPost, pk=pk, business=business)
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:list')
    else:
        form = BlogPostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
        'active_tab': 'blog',
        'title': 'Blogni Tahrirlash'
    }
    return render(request, 'dashboard/blog/form.html', context)


@login_required
@require_http_methods(["POST"])
def blog_delete(request, pk):
    """Blog post'ni o'chirish"""
    try:
        business = request.user.business
    except:
        return redirect('dashboard:home')
    
    post = get_object_or_404(BlogPost, pk=pk, business=business)
    post.delete()
    return redirect('blog:list')


# ─── Public Views (Foydalanuvchilar uchun) ────────────────────────────────

@require_http_methods(["GET"])
def blog_public_list(request, slug):
    """Biznesning blog postlarini foydalanuvchilarga ko'rsatish"""
    from business.models import Business
    business = get_object_or_404(Business, slug=slug, is_active=True)
    posts = business.blog_posts.filter(is_published=True)
    
    paginator = Paginator(posts, 6)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'business': business,
        'posts': posts,
    }
    return render(request, 'public/blog_list.html', context)


@require_http_methods(["GET", "POST"])
def blog_public_detail(request, slug, post_slug):
    """Blog post'ni to'liq ko'rish va izohlar qo'shish"""
    from business.models import Business
    business = get_object_or_404(Business, slug=slug, is_active=True)
    post = get_object_or_404(BlogPost, slug=post_slug, business=business, is_published=True)
    
    # Views count'ni oshirish
    post.views_count += 1
    post.save(update_fields=['views_count'])
    
    # Izohlarni olish
    comments = post.comments.filter(is_approved=True)
    
    if request.method == 'POST':
        form = BlogCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('public-blog-detail', slug=slug, post_slug=post_slug)
    else:
        form = BlogCommentForm()
    
    context = {
        'business': business,
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'public/blog_detail.html', context)
