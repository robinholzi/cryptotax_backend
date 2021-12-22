from functools import wraps

from cryptotax_backend.utils import error_response


def ensure_authenticated_user(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_active:
            return error_response(401, 0, "not authenticated or verified.")

        return function(request, *args, **kwargs)

    return wrap
