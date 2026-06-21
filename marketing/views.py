from django.shortcuts import render


def home(request):
    return render(request, 'marketing/home.html')

def features(request):
    return render(request, 'marketing/features.html')

def pricing(request):
    return render(request, 'marketing/pricing.html')

def faq(request):
    return render(request, 'marketing/faq.html')

def contact(request):
    return render(request, 'marketing/contact.html')
