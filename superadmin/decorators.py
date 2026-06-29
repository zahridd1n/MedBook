from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def superuser_required(view_func):
    """
    Decorator that restricts a view to superusers only.
    Redirects unauthenticated or non-superusers to login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            from django.urls import reverse
            return redirect(f"{reverse('accounts:login')}?next={request.path}")
        return view_func(request, *args, **kwargs)
    return wrapper
