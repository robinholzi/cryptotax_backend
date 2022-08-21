import logging
from typing import (
    Any,
    Callable,
)

from rest_framework.request import Request

from utils.exceptions.exceptions import APIException
from utils.response_wrappers import error_response

logger = logging.getLogger(__name__)


def exception_handler(
    function: Callable[..., dict[str, Any]]
) -> Callable[..., dict[str, Any]]:
    def wrap(
        request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
    ) -> dict[str, Any]:
        try:
            return function(request, *args, **kwargs)

        except KeyError as e:
            logging.exception(e)
            return error_response(
                status=500,
                code=0,
                title="Unhandled exception: KeyError!",
                message="Sorry, your request caused an unexpected exception on our side!",
            )
        except TypeError as e:
            logging.exception(e)
            return error_response(
                status=500,
                code=0,
                title="Unhandled exception: TypeError!",
                message="Sorry, your request caused an unexpected exception on our side!",
            )
        except ValueError as e:
            logging.exception(e)
            return error_response(
                status=500,
                code=0,
                title="Unhandled exception: ValueError!",
                message="Sorry, your request caused an unexpected exception on our side!",
            )
        except APIException as e:
            logging.exception(e)
            return error_response(
                status=e.status_code,
                code=e.error_code,
                title=e.message,
                message=e.detail,
            )
        except Exception as e:
            logging.exception(e)
            return error_response(
                status=500,
                code=0,
                title="Unhandled exception on our side!",
                message="Sorry, your request caused an unexpected exception on our side!",
            )
        except BaseException as e:
            logging.exception(e)
            return error_response(
                status=500,
                code=0,
                title="Unhandled exception on our side!",
                message="Sorry, your request caused an unexpected exception on our side!",
            )

    return wrap
