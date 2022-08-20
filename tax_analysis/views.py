from time import sleep
from typing import Any

from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from tax_analysis.analysis_worker.analysis_worker import analysis_worker
from tax_analysis.analysis_worker.processor_worker import processable_worker
from utils.response_wrappers import (
    error_response,
    success_response,
)


@api_view(["POST"])
def fetch_processable_view(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    loop = int(request.GET.get("repeat", "1"))
    try:
        for i in range(0, loop):
            print(f"fetch_processable_view iteration: ${i}")
            processable_worker()
            sleep(0.005)

        return success_response(200, 0, "fetch_processable_view successfully.")

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )


@api_view(["POST"])
def analyser_view(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    loop = int(request.GET.get("repeat", "1"))
    try:
        for i in range(0, loop):
            print(f"analyser_view iteration: ${i}")
            analysis_worker()
            sleep(0.005)

        return success_response(200, 0, "analyser_view successfully.")

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )
