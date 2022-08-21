from django.urls import path

from user.auth_views import (
    password_reset,
    password_reset_done,
)
from user.views import (
    login_view,
    signup_resend_email,
    signup_view,
)

app_name = "auth"


urlpatterns = [
    # =======================================================================================
    path("login/", login_view, name="login"),
    path("signup/", signup_view, name="signup"),
    path("signup_resend_email/", signup_resend_email, name="signup_resend_email"),
    path("password/reset/", password_reset, name="password_reset"),
    path("password/reset/done", password_reset_done, name="password_reset_done"),
    # path('password/reset/confirm/',
    #      PasswordResetConfirmView.as_view(),
    #      name='password_reset_confirm'),  # password_reset_confirm
    # TODO password change when signed in
    # =======================================================================================
]
