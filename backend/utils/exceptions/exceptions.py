class APIException(Exception):
    def __init__(
        self,
        message: str = "Internal Server Error - base APIException",
        detail: str = "",
        status_code: int = 500,
        error_code: int = 0,
    ):
        self.message = message
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code


class APIExceptionBadRequest(APIException):
    def __init__(
        self,
        message: str = "Bad Request",
        detail: str = "",
        status_code: int = 400,
        error_code: int = 0,
    ):
        super().__init__(message, detail, status_code, error_code)


class DataBaseException(APIException):
    def __init__(
        self,
        message: str = "Database Error",
        detail: str = "",
        status_code: int = 500,
        error_code: int = 0,
    ):
        super().__init__(message, detail, status_code, error_code)


class APIExceptionNotFound(APIException):
    def __init__(
        self,
        message: str = "Not Found",
        detail: str = "",
        status_code: int = 404,
        error_code: int = 0,
    ):
        super().__init__(message, detail, status_code, error_code)


class APIExceptionInternal(APIException):
    def __init__(
        self,
        message: str = "Internal Server Error",
        detail: str = "",
        status_code: int = 500,
        error_code: int = 0,
    ):
        super().__init__(message, detail, status_code, error_code)
