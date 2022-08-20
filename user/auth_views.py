from typing import Any

from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.request import Request

from user.auth_forms import PasswordResetForm
from user.models import CryptoTaxUser
from user.tokens import email_verification_token_generator
from utils.response_wrappers import (
    error_response,
    success_response,
)


@api_view(["GET"])
def activate_view(
    request: Request,
    uidb64: str,
    token: str,
    *args: tuple[Any, ...],
    **kwargs: tuple[Any, ...]
) -> HttpResponse:
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = CryptoTaxUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CryptoTaxUser.DoesNotExist):
        user = None
    if user is not None and email_verification_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        context = {
            "msg_type": 1,
            "msg": "Thank you for your email confirmation. Now you can login your account.",
            "link": request.scheme
            + "://"
            + get_current_site(request).domain
            + "/auth/login/",
            "link_text": "Login",
        }
        return render(request, "base_notification.html", context)
    else:
        context = {
            "msg_type": 3,
            "msg": "Email Verification failed! Token invalid or user not existing!",
            "link": request.scheme + "://" + get_current_site(request).domain + "/",
            "link_text": "To Start",
        }
        return render(request, "base_notification.html", context)


# todo 2-5 minute cooldown
@api_view(["POST"])
# @ratelimit(key='post:email', rate='6/d')
def password_reset(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> HttpResponse:
    form = PasswordResetForm(request.POST)
    if form.is_valid():
        form.save(request=request)
        return success_response(200, 0, "password reset email sent")
    # return redirect("/auth/password/reset_sent/")
    return error_response(400, 0, "form error", data=form.errors)


@api_view(["GET"])
def password_reset_done(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> HttpResponse:
    return success_response(200, 0, "password reset email sent")


@require_http_methods(["GET"])
def password_reset_complete(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> HttpResponse:
    context = {
        "msg_type": 1,
        "msg": "Password reset successful.",
        "link": request.scheme
        + "://"
        + get_current_site(request).domain
        + "/auth/login/",
        "link_text": "Login",
    }
    return render(request, "base_notification.html", context)
