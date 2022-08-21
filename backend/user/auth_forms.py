from typing import (
    Any,
    Optional,
)

from django import forms
from django.contrib.auth import (
    authenticate,
    get_user_model,
)
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField,
    SetPasswordForm,
)
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import capfirst
from rest_framework.authtoken.management.commands.drf_create_token import UserModel
from rest_framework.request import Request

from user.auth import send_signup_email
from user.models import CryptoTaxUser
from utils.mail_utils import send_mail


class SingUpForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """

    email = forms.EmailField(max_length=750)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = CryptoTaxUser
        fields = ("email", "username", "first_name", "last_name")

    def save(
        self,
        commit: bool = True,
        domain_override: Any = None,
        use_https: bool = False,
        token_generator: Any = default_token_generator,
        from_email: str = None,
        request: Request = None,
    ) -> CryptoTaxUser:
        user: CryptoTaxUser = super(SingUpForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = False
        if commit:
            user.save()

        send_signup_email(
            request, user, from_email, domain_override
        )  # TODO multilang emails
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text="Raw passwords are not stored, so there is no way to see "
        "this user's password, but you can change the password "
        'using <a href="password/">this form</a>.',
    )

    class Meta:
        model = CryptoTaxUser
        fields = "__all__"

    def __init__(self, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get("user_permissions", None)
        if f is not None:
            f.queryset = f.queryset.select_related("content_type")

    def clean_password(self) -> str:
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class AuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """

    username = forms.CharField(max_length=254)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    error_messages = {
        "invalid_login": "Please enter a correct %(username)s and password. "
        "Note that both fields may be case-sensitive.",
        "inactive": "This account is inactive.",
    }

    def __init__(
        self, request: Request = None, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
    ):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super(AuthenticationForm, self).__init__(*args, **kwargs)

        # Set the label for the "username" field.
        user_model = get_user_model()
        self.username_field = user_model._meta.get_field(UserModel.USERNAME_FIELD)
        if self.fields["username"].label is None:
            self.fields["username"].label = capfirst(self.username_field.verbose_name)

    def clean(self) -> dict:
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                    params={"username": self.username_field.verbose_name},
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user: CryptoTaxUser) -> None:
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )

    def get_user_id(self) -> Optional[int]:
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self) -> Any:
        return self.user_cache


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=750)

    def get_users(self, email: str) -> Any:
        """Given an user, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.

        """
        active_users = CryptoTaxUser.objects.filter(email__iexact=email, is_active=True)
        return (u for u in active_users if u.has_usable_password())

    def save(
        self,
        domain_override: Any = None,
        subject_template_name: str = "registration/password_reset_subject.txt",
        email_template_name: str = "user/password_reset_email.html",
        use_https: Any = False,
        token_generator: Any = default_token_generator,
        from_email: str = None,
        request: Optional[Request] = None,
        html_email_template_name: str = None,
    ) -> None:
        """Generates a one-use only link for resetting password and sends to the user."""
        pass
        email = self.cleaned_data["email"]
        for user in self.get_users(email):
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
                "token": token_generator.make_token(user),
                "protocol": request.scheme if request is not None else "http",
            }

            # TODO multilang emails
            send_mail(
                context,
                from_email,
                user.email,
                "email/user/password_reset_email_subject.txt",
                "email/user/password_reset_email.txt",
                html_email_template_name="email/user/password_reset_email.html",
            )


# class SetPasswordForm(forms.Form):
#     """
#     A form that lets a user change set their password without entering the old
#     password
#     """
#     error_messages = {
#         'password_mismatch': "The two password fields didn't match.",
#     }
#     new_password1 = forms.CharField(label="New password",
#                                     widget=forms.PasswordInput)
#     new_password2 = forms.CharField(label="New password confirmation",
#                                     widget=forms.PasswordInput)
#
#     def __init__(self, user, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]):
#         self.user = user
#         super(SetPasswordForm, self).__init__(*args: tuple[Any, ...], **kwargs: tuple[Any, ...])
#
#     def clean_new_password2(self):
#         password1 = self.cleaned_data.get('new_password1')
#         password2 = self.cleaned_data.get('new_password2')
#         if password1 and password2:
#             if password1 != password2:
#                 raise forms.ValidationError(
#                     self.error_messages['password_mismatch'],
#                     code='password_mismatch',
#                 )
#         return password2
#
#     def save(self, commit=True):
#         self.user.set_password(self.cleaned_data['new_password1'])
#         if commit:
#             self.user.save()
#         return self.user
#


class PasswordChangeForm(SetPasswordForm):
    """
    A form that lets a user change their password by entering their old
    password.
    """

    error_messages = dict(
        SetPasswordForm.error_messages,
        **{
            "password_incorrect": (
                "Your old password was entered incorrectly. " "Please enter it again."
            ),
        }
    )
    old_password = forms.CharField(label="Old password", widget=forms.PasswordInput)

    def clean_old_password(self) -> str:
        """
        Validates that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages["password_incorrect"],
                code="password_incorrect",
            )
        return old_password


class AdminPasswordChangeForm(forms.Form):
    """
    A form used to change the password of a user in the admin interface.
    """

    error_messages = {
        "password_mismatch": "The two password fields didn't match.",
    }
    required_css_class = "required"
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
    )

    def __init__(
        self, user: CryptoTaxUser, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
    ):
        self.user = user
        super(AdminPasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_password2(self) -> str:
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages["password_mismatch"],
                    code="password_mismatch",
                )
        return password2

    def save(self, commit: bool = True) -> CryptoTaxUser:
        """
        Saves the new password.
        """
        self.user.set_password(self.cleaned_data["password1"])
        if commit:
            self.user.save()
        return self.user

    def _get_changed_data(self) -> list[str]:
        data = super(AdminPasswordChangeForm, self).changed_data
        for name in self.fields.keys():
            if name not in data:
                return []
        return ["password"]

    changed_data = property(_get_changed_data)
