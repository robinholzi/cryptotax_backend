from typing import Any

from rest_framework.response import Response


def error_response(
    status: int, code: int, title: str, message: str = None, data: Any = None
) -> Response:
    context = {
        "code": code,
        "title": title,
        "message": message,
        "data": data,
    }
    return Response(context, status=status)


def success_response(
    status: int, code: int, title: str, message: str = None, data: Any = None
) -> Response:
    context = {
        "code": code,
        "title": title,
        "message": message,
        "data": data,
    }
    return Response(context, status=status)
