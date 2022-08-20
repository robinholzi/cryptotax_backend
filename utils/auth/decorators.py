from functools import wraps
from typing import (
    Any,
    Callable,
)

from rest_framework.request import Request
from rest_framework.response import Response

from utils.response_wrappers import error_response


def ensure_authenticated_user(function: Callable) -> Response:
    @wraps(function)
    def wrap(
        request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
    ) -> Response:
        if not request.user.is_authenticated or not request.user.is_active:
            return error_response(401, 0, "not authenticated or verified.")

        return function(request, *args, **kwargs)

    return wrap
