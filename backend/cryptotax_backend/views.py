from typing import Any

from django.core.mail import EmailMultiAlternatives
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
)
from rest_framework.request import Request
from rest_framework.response import Response

from user.auth import send_signup_email
from utils.auth.decorators import ensure_authenticated_user
from utils.exceptions.exception_handlers import exception_handler
from utils.response_wrappers import (
    error_response,
    success_response,
)


@api_view(["GET"])
@exception_handler
def test(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    return success_response(200, 0, "test successful!")


@api_view(["GET"])
@exception_handler
def send_test_mail(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    subject = "CryptoTax Django Test mail!"
    body = "Test Content"
    email_message = EmailMultiAlternatives(
        subject, body, "nerotecs@gmail.com", ["rnholzinger01@gmail.com"]
    )
    email_message.send()
    return success_response(200, 0, "sending successful!")


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@exception_handler
@ensure_authenticated_user
def send_test_mail2(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        send_signup_email(request, request.user, "nerotecs@gmail.com")
        return success_response(200, 0, "sending successful!")

    except Exception as er:
        print("Error sending email: ", er)
        return error_response(500, 0, "unknown error!")
