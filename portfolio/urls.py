from django.urls import path, include

from portfolio.views import create_order_list

urlpatterns = [
    path('order/create/', create_order_list, name="create_order_list"),
]
