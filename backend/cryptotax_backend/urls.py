"""cryptotax_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import (
    include,
    path,
)

from cryptotax_backend.views import (
    send_test_mail,
    send_test_mail2,
    test,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/test/", test, name="test"),
    path("api/v1/portfolio/", include("portfolio.urls"), name="api_v1_portfolio"),
    path("api/v1/user/", include("user.urls"), name="user"),
    path("auth/", include("user.auth_urls"), name="user_auth"),
    path(
        "api/v1/dev/analysis/", include("tax_analysis.urls"), name="api_v1_dev_analysis"
    ),
    path("api/v1/dev/send_test_mail/", send_test_mail, name="send_test_mail"),
    path("api/v1/dev/send_test_mail2/", send_test_mail2, name="send_test_mail2"),
]
