from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import path
from rest_framework.reverse import reverse_lazy

from user.auth_views import (
    activate_view,
    password_reset_complete,
)

app_name = "user_auth"

# urls which have django based webviews (not react frontend)
urlpatterns = [
    # =======================================================================================
    path("activate/<uidb64>/<token>/", activate_view, name="activate"),
    path(
        "password/reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="user/password_reset_confirm.html",
            success_url=reverse_lazy("user_auth:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        password_reset_complete,
        name="password_reset_complete",
    ),
    # =======================================================================================
]
