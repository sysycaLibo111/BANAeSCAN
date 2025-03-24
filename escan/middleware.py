from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        restricted_urls = {
            'admin_dashboard': 'Admin',
            'user_dashboard': 'User',
        }

        if request.user.is_authenticated:
            for view_name, required_role in restricted_urls.items():
                if request.path.startswith(reverse(view_name)) and request.user.role != required_role:
                    return redirect('login')

        return self.get_response(request)


def supabase_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")  
        return view_func(request, *args, **kwargs)
    return wrapper
