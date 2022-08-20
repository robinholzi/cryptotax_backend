from django.urls import path

from tax_analysis.views import (
    analyser_view,
    fetch_processable_view,
)

urlpatterns = [
    path("fetch_processable/", fetch_processable_view, name="api_v1_dev_analysis"),
    path("analyze/", analyser_view, name="api_v1_dev_analysis2"),
    path("clean_analysis/", analyser_view, name="api_v1_dev_analysis2"),
    path("update_modes/", analyser_view, name="api_v1_dev_analysis2"),
]
