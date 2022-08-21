from typing import Any

from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from jsonschema import ValidationError
from rest_framework import serializers

from user.models import CryptoTaxUser
from user.view_helpers.auth_backend import EmailOrUsernameModelBackend


class AuthTokenSerializer(serializers.Serializer):
    email_username = serializers.CharField(label=_("Email/Username"), write_only=True)
    password = serializers.CharField(
        label=_("Password"),
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )
    token = serializers.CharField(label=_("Token"), read_only=True)

    class Meta:
        fields = ["email_username", "password"]
        validators: list[Any] = []

    def validate_email_username(self, value: str) -> str:
        if not value or len(value) < 1:
            raise ValidationError("email is required!")
        return value

    def validate_password(self, value: str) -> str:
        if not value or len(value) < 1:
            raise ValidationError("password is required!")
        return value

    def validate(self, attrs: dict) -> dict:
        email_username = attrs.get("email_username")
        password = attrs.get("password")

        if email_username and password:
            user = EmailOrUsernameModelBackend().authenticate(
                email_username=email_username, password=password
            )

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _("Unable to log in with provided credentials.")
                raise serializers.ValidationError(msg, code="auth")
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class AuthTokenPasswordlessSerializer(serializers.Serializer):
    email_username = serializers.CharField(label=_("Email/Username"), write_only=True)

    class Meta:
        fields = ["email_username"]
        validators: list[Any] = []

    def validate_email_username(self, value: str) -> str:
        if not value or len(value) < 1:
            raise ValidationError("email is required!")
        return value

    def validate(self, attrs: dict) -> dict:
        email_username = attrs.get("email_username")
        # password = attrs.get("password")

        if email_username:
            query = CryptoTaxUser.objects.filter(
                Q(email__iexact=email_username) | Q(username__iexact=email_username)
            )

            if not query.exists():
                msg = _("No user found!")
                raise serializers.ValidationError(msg, code="auth")

            query = query.filter(is_active=False)

            if not query.exists():
                msg = _("No user found which is not already verified!")
                raise serializers.ValidationError(msg, code="auth")

        else:
            msg = _('Must include "email/username".')
            raise serializers.ValidationError(msg, code="authorization")

        attrs["users"] = query.all()
        return attrs
