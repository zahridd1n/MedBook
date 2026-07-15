from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from .models import BlogPost, BlogComment
from .forms import BlogPostForm, BlogCommentForm
from business.models import Business


@login_required
@require_http_methods(["GET"])
def blog_list(request):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('dashboard:home')

    posts = business.blog_posts.all()
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)

    return render(request, 'dashboard/blog/list.html', {
        'business': business,
        'posts': posts,
        'active_tab': 'blog',
    })


@login_required
@require_http_methods(["GET", "POST"])
def blog_create(request):
    try:
        business = request.user.business
    except Business.DoesNotExist:
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

    return render(request, 'dashboard/blog/form.html', {
        'form': form,
        'business': business,
        'active_tab': 'blog',
        'title': _('Yangi Blog Qo\'shish'),
    })


@login_required
@require_http_methods(["GET", "POST"])
def blog_edit(request, pk):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('dashboard:home')

    post = get_object_or_404(BlogPost, pk=pk, business=business)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:list')
    else:
        form = BlogPostForm(instance=post)

    return render(request, 'dashboard/blog/form.html', {
        'form': form,
        'post': post,
        'business': business,
        'active_tab': 'blog',
        'title': _('Blogni Tahrirlash'),
    })


@login_required
@require_http_methods(["POST"])
def blog_delete(request, pk):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('dashboard:home')

    post = get_object_or_404(BlogPost, pk=pk, business=business)
    post.delete()
    return redirect('blog:list')


@require_http_methods(["GET"])
def blog_public_list(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    posts = business.blog_posts.filter(is_published=True)

    paginator = Paginator(posts, 6)
    page = request.GET.get('page')
    posts = paginator.get_page(page)

    return render(request, 'public/blog_list.html', {
        'business': business,
        'posts': posts,
    })


@require_http_methods(["GET", "POST"])
def blog_public_detail(request, slug, post_slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    post = get_object_or_404(BlogPost, slug=post_slug, business=business, is_published=True)

    post.views_count += 1
    post.save(update_fields=['views_count'])

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

    return render(request, 'public/blog_detail.html', {
        'business': business,
        'post': post,
        'comments': comments,
        'form': form,
    })


@login_required
@require_http_methods(["GET"])
def comment_list(request):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('dashboard:home')

    comments = BlogComment.objects.filter(post__business=business).order_by('-created_at')
    return render(request, 'dashboard/blog/comment_list.html', {
        'business': business,
        'comments': comments,
        'active_tab': 'blog',
    })


@login_required
@require_http_methods(["POST"])
def comment_approve(request, pk):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('dashboard:home')

    comment = get_object_or_404(BlogComment, pk=pk, post__business=business)
    comment.is_approved = True
    comment.save(update_fields=['is_approved'])
    return redirect('blog:comment-list')


@login_required
@require_http_methods(["POST"])
def comment_delete(request, pk):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('dashboard:home')

    comment = get_object_or_404(BlogComment, pk=pk, post__business=business)
    comment.delete()
    return redirect('blog:comment-list')

