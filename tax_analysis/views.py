import datetime

from django.shortcuts import render
from rest_framework.decorators import api_view

from cryptotax_backend.utils import error_response, success
from tax_analysis.analysis_worker.processor_worker import processable_worker


@api_view(['POST'])
def fetch_processable_view(request, *args, **kwargs):
    try:
        processable_worker()

        return success(200, 0, "create_order_list successfully.")

    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.", )
