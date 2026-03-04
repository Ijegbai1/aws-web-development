from django.http import HttpResponseForbidden
from functools import wraps

def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Login required")
            if request.user.role not in roles:
                return HttpResponseForbidden("Not allowed")
            return view(request, *args, **kwargs)
        return _wrapped
    return decorator