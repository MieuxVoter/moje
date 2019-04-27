from django.shortcuts import render, get_object_or_404
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import resolve_url
from django.utils.decorators import available_attrs, method_decorator
from django.conf import settings
from django.contrib.auth.views import redirect_to_login


from vote.models import *

def basics_authenticated(login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary.
    If authenticated, it loads basics parameters
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                params = basics_params(request)
                (template_path, view_params) = view_func(request, *args, **kwargs)
                params.update(view_params)
                return render(request, template_path, params)
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()

            return redirect_to_login(
                path, resolved_login_url, redirect_field_name)
        return _wrapped_view
    return decorator


def get_voter(request):
    voter = get_object_or_404(Voter, user=request.user)
