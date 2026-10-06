from functools import wraps
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode


def staff_required(view):
    """Only logged-in staff may open dashboard pages; others go to the dashboard login."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and user.is_staff and user.is_active:
            return view(request, *args, **kwargs)
        login_url = reverse('dashboard:login')
        query = urlencode({REDIRECT_FIELD_NAME: request.get_full_path()})
        return redirect(f"{login_url}?{query}")
    return wrapper
