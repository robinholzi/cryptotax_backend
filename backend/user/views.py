"""
ERRORS:
- 200:
    0: login successful
- 400:
    field_errors
    non_field_errors
- 401:
    0: email not verified, yet.
"""
from typing import Any

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from user.auth import send_signup_email
from user.auth_forms import SingUpForm
from user.view_helpers.auth_serializer import (
    AuthTokenPasswordlessSerializer,
    AuthTokenSerializer,
)
from utils.exceptions.exception_handlers import exception_handler
from utils.response_wrappers import (
    error_response,
    success_response,
)


@api_view(["POST"])
# TODO; catcha to avoid brute force blocks
# @ratelimit(key='ip', rate='10/s')
def login_view(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    serializer = AuthTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(400, 0, "form error", data=serializer.errors)

    user = serializer.validated_data["user"]
    if user.is_active:
        token, created = Token.objects.get_or_create(user=user)
        return success_response(
            200,
            0,
            "login successful",
            data={
                "email": user.email,
                "username": user.username,
                "token": token.key,
            },
        )
    else:
        return error_response(
            401,
            0,
            title="email not verified, yet.",
            data={
                "email": user.email,
                "username": user.username,
            },
        )


@api_view(["POST"])
def signup_view(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    form = SingUpForm(request.POST)
    if form.is_valid():
        user = form.save(request=request)
        return success_response(
            200,
            0,
            "account created.",
            "Please confirm your email address to complete the registration.",
            data={
                "email": user.email,
                "username": user.username,
            },
        )
    return error_response(400, 0, "form error", data=form.errors)


# TODO rate limit!
@api_view(["POST"])
@exception_handler()
def signup_resend_email(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    serializer = AuthTokenPasswordlessSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response(400, 0, "form error", data=serializer.errors)

    users = serializer.validated_data["users"]
    for user in users:
        send_signup_email(request, user)

    return success_response(200, 0, "email(s) sent")
