import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from business.models import Business, WorkingHours
from blog.models import BlogPost
from services.models import Service
from employees.models import Employee
from customers.models import Customer
from appointments.models import Appointment

def generate():
    User = get_user_model()
    
    # 1. Create a primary user for the main business
    main_user, _ = User.objects.get_or_create(email="main_tester@example.com", defaults={
        "first_name": "Main",
        "last_name": "Tester",
        "is_active": True
    })
    if not main_user.password:
        main_user.set_password("testpass123")
        main_user.save()

    # 2. Create the main business
    main_biz, created = Business.objects.get_or_create(slug="main-test-biz", defaults={
        "owner": main_user,
        "name": "Super Pagination Business",
        "about": "This business is created to test pagination. It has a lot of data.",
        "city": "Tashkent",
        "category": "beauty",
        "subscription_plan": "enterprise",
        "is_active": True,
        "show_in_directory": True
    })
    
    if created:
        for d in range(7):
            WorkingHours.objects.create(business=main_biz, day=d, is_open=True)

    print(f"Main business ID: {main_biz.id}, Name: {main_biz.name}")

    # 3. Create 6-7 other test businesses for the directory
    for i in range(1, 8):
        u, _ = User.objects.get_or_create(email=f"tester{i}@example.com", defaults={
            "first_name": f"Test{i}",
            "last_name": "User",
            "is_active": True
        })
        biz, biz_created = Business.objects.get_or_create(slug=f"test-biz-{i}", defaults={
            "owner": u,
            "name": f"Test Business {i}",
            "about": f"Just a dummy business number {i}",
            "city": random.choice(["Tashkent", "Samarkand", "Bukhara", "Andijan"]),
            "category": random.choice(["beauty", "medical", "sport", "education", "other"]),
            "subscription_plan": random.choice(["free", "growth", "enterprise"]),
            "is_active": True,
            "show_in_directory": True
        })
        if biz_created:
            for d in range(7):
                WorkingHours.objects.create(business=biz, day=d, is_open=(d < 5))
                
    print("Created 7 other businesses.")

    # 4. Generate lots of data for main_biz
    # 20 blogs (paginator is 6 on public, 10 on dashboard) -> creates 3-4 pages
    if main_biz.blog_posts.count() < 20:
        for i in range(20 - main_biz.blog_posts.count()):
            BlogPost.objects.create(
                business=main_biz,
                title=f"Test Article {i+1}",
                slug=f"test-article-{i+1}",
                content=f"This is the content for test article {i+1}. " * 10,
                is_published=True
            )
        print("Generated 20 blog posts.")

    # 30 services (paginator is 15) -> 2 pages
    if main_biz.services.count() < 30:
        for i in range(30 - main_biz.services.count()):
            Service.objects.create(
                business=main_biz,
                name=f"Service {i+1}",
                duration=random.choice([30, 60, 90, 120]),
                price=random.randint(10, 100) * 1000,
                is_active=True
            )
        print("Generated 30 services.")

    # 25 employees (paginator is 15) -> 2 pages
    if main_biz.employees.count() < 25:
        services = list(main_biz.services.all())
        for i in range(25 - main_biz.employees.count()):
            emp = Employee.objects.create(
                business=main_biz,
                name=f"Employee {i+1}",
                position="Specialist",
                is_active=True
            )
            if services:
                emp.services.set(random.sample(services, k=min(3, len(services))))
        print("Generated 25 employees.")

    # 40 customers (paginator is 15) -> 3 pages
    if main_biz.customers.count() < 40:
        for i in range(40 - main_biz.customers.count()):
            Customer.objects.create(
                business=main_biz,
                full_name=f"Customer {i+1} Name",
                phone=f"+99890{random.randint(1000000, 9999999)}"
            )
        print("Generated 40 customers.")
        
    print("Data generation complete!")

if __name__ == '__main__':
    generate()
