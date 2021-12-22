
from django.utils.translation import gettext_lazy as _
from jsonschema import ValidationError

from rest_framework import serializers

from user.view_helpers.auth_backend import EmailOrUsernameModelBackend


class AuthTokenSerializer(serializers.Serializer):
    email_username = serializers.CharField(
        label=_("Email/Username"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    class Meta:
        fields = ['email_username', 'password']
        validators = []

    def validate_email_username(self, value):
        if not value or len(value) < 1:
            raise ValidationError("email is required!")
        return value

    def validate_password(self, value):
        if not value or len(value) < 1:
            raise ValidationError("password is required!")
        return value

    def validate(self, attrs):
        email_username = attrs.get('email_username')
        password = attrs.get('password')

        if email_username and password:
            user = EmailOrUsernameModelBackend.authenticate(email_username=email_username, password=password)

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='auth')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
