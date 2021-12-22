
from django.contrib import admin
from django.urls import path, include

from tax_analysis.views import fetch_processable_view

urlpatterns = [

    path('fetch_processable/', fetch_processable_view, name="api_v1_dev_analysis"),

]
