import logging
from typing import (
    Any,
    Callable,
    Optional,
)

from django.db import IntegrityError
from rest_framework.request import Request

from utils.exceptions.exceptions import (
    APIException,
    DataBaseException,
)
from utils.response_wrappers import error_response

logger = logging.getLogger(__name__)


def exception_handler(message: Optional[str] = None) -> Callable:
    def outer_wrapper(function: Callable) -> Callable:
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
                    message=message
                    or "Sorry, your request caused an unexpected exception on our side!",
                )
            except TypeError as e:
                logging.exception(e)
                return error_response(
                    status=500,
                    code=0,
                    title="Unhandled exception: TypeError!",
                    message=message
                    or "Sorry, your request caused an unexpected exception on our side!",
                )
            except ValueError as e:
                logging.exception(e)
                return error_response(
                    status=500,
                    code=0,
                    title="Unhandled exception: ValueError!",
                    message=message
                    or "Sorry, your request caused an unexpected exception on our side!",
                )
            except DataBaseException as e:
                logging.exception(e)
                return error_response(
                    status=e.status_code,
                    code=e.error_code,
                    title=e.message,
                    message=message or e.detail,
                )
            except APIException as e:
                logging.exception(e)
                return error_response(
                    status=e.status_code,
                    code=e.error_code,
                    title=e.message,
                    message=message or e.detail,
                )
            except Exception as e:
                logging.exception(e)
                return error_response(
                    status=500,
                    code=0,
                    title="Unhandled exception on our side!",
                    message=message
                    or "Sorry, your request caused an unexpected exception on our side!",
                )
            except BaseException as e:
                logging.exception(e)
                return error_response(
                    status=500,
                    code=0,
                    title="Unhandled exception on our side!",
                    message=message
                    or "Sorry, your request caused an unexpected exception on our side!",
                )

        return wrap

    return outer_wrapper


def db_exception_handler(
    message: Optional[str] = None,
) -> Callable:
    def outer_wrapper(function: Callable) -> Callable:
        def wrap(
            request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
        ) -> dict[str, Any]:
            try:
                return function(request, *args, **kwargs)

            except IntegrityError as e:
                logging.exception(e)
                raise DataBaseException(
                    message or "Unexpected exception during database"
                )
            except Exception as e:
                logging.exception(e)
                raise DataBaseException(
                    message or "Unexpected exception during database"
                )
            except BaseException as e:
                logging.exception(e)
                raise DataBaseException(
                    message or "Unexpected exception during database"
                )

        return wrap

    return outer_wrapper
