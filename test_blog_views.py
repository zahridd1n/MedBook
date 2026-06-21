#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from business.models import Business
from django.template.loader import render_to_string
from django.core.paginator import Paginator

business = Business.objects.first()

print(f"Business: {business.name} (slug: {business.slug})")

# Simulate what blog_public_list does
print("\n" + "=" * 60)
print("SIMULATING blog_public_list")
print("=" * 60)

posts_queryset = business.blog_posts.filter(is_published=True)
print(f"Posts queryset count: {posts_queryset.count()}")
print(f"Posts: {list(posts_queryset.values_list('title', 'is_published'))}")

paginator = Paginator(posts_queryset, 6)
page = None  # No page parameter
posts_page = paginator.get_page(page)

print(f"Page object: {posts_page}")
print(f"Page count: {len(posts_page)}")
print(f"Paginator count: {posts_page.paginator.count}")
print(f"bool(posts_page): {bool(posts_page)}")

context = {
    'business': business,
    'posts': posts_page,
}

# Try rendering the template
try:
    html = render_to_string('public/blog_list.html', context)
    print(f"\nTemplate rendered successfully")
    print(f"HTML length: {len(html)}")
    
    if 'empty-state' in html:
        print("✗ Empty state is being shown")
        # Find and print the empty state section
        idx = html.find('empty-state')
        if idx > 0:
            print(f"Empty state HTML:\n{html[max(0, idx-100):idx+300]}")
    else:
        print("✓ Empty state not shown")
        
    if 'row g-4' in html:
        print("✓ Blog cards HTML found")
        # Count posts
        post_count = html.count('<div class="col-md-6 col-lg-4">')
        print(f"  Blog card divs found: {post_count}")
    else:
        print("✗ No blog cards found")
        
except Exception as e:
    print(f"Error rendering template: {e}")
    import traceback
    traceback.print_exc()

# Now test detail
print("\n" + "=" * 60)
print("SIMULATING blog_public_detail")
print("=" * 60)

post = business.blog_posts.filter(is_published=True).first()
if post:
    print(f"Post: {post.title}")
    print(f"Post slug: {post.slug}")
    print(f"Post content length: {len(post.content)}")
    
    context_detail = {
        'business': business,
        'post': post,
        'comments': post.comments.filter(is_approved=True),
        'form': None,
    }
    
    try:
        html = render_to_string('public/blog_detail.html', context_detail)
        print(f"Template rendered successfully")
        print(f"HTML length: {len(html)}")
        
        if post.title in html:
            print(f"✓ Post title found in HTML")
        else:
            print(f"✗ Post title NOT in HTML")
            
        # Check for content
        if post.content[:50] in html:
            print(f"✓ Post content found in HTML")
        else:
            print(f"✗ Post content NOT in HTML")
            
    except Exception as e:
        print(f"Error rendering template: {e}")
        import traceback
        traceback.print_exc()




