from typing import Optional

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.request import Request

from user.models import CryptoTaxUser
from user.tokens import email_verification_token_generator
from utils.mail_utils import send_mail


def send_signup_email(
    request: Request,
    user: CryptoTaxUser,
    from_email: Optional[str] = None,
    domain_override: Optional[str] = None,
) -> None:
    if not domain_override:
        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain
    else:
        site_name = domain = domain_override
    context = {
        "email": user.email,
        "name": user.first_name + " " + (user.last_name or "?")[0] + ".",
        "username": user.username,
        "domain": domain,
        "site_name": site_name,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": email_verification_token_generator.make_token(user),
        "protocol": request.scheme,
    }

    send_mail(
        context,
        from_email,
        user.email,
        "email/user/email_verification_subject.txt",
        "email/user/email_verification_email.txt",
        html_email_template_name="email/user/email_verification_email.html",
    )
