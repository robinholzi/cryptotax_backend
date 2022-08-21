from typing import (
    Any,
    Optional,
)

from django.core.mail import EmailMultiAlternatives
from django.template import loader


def send_mail(
    context: dict[str, str],
    from_email: Optional[str],
    to_email: Optional[str],
    subject_template_name: Optional[str],
    email_template_name: Optional[str],
    html_email_template_name: Optional[str] = None,
) -> Any:
    """
    Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
    """
    subject = loader.render_to_string(subject_template_name, context)
    subject = "".join(subject.splitlines())  # Email subject *must not* contain newlines
    body = loader.render_to_string(email_template_name, context)
    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, "text/html")

    email_message.send()
