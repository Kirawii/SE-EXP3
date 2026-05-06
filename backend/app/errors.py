from fastapi import status
from fastapi.requests import Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    code: str = "domain_error"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__


class UsernameTaken(DomainError):
    code = "username_taken"
    status_code = status.HTTP_409_CONFLICT


class EmailTaken(DomainError):
    code = "email_taken"
    status_code = status.HTTP_409_CONFLICT


class InvalidCredentials(DomainError):
    code = "invalid_credentials"
    status_code = status.HTTP_401_UNAUTHORIZED


class TokenInvalid(DomainError):
    code = "token_invalid"
    status_code = status.HTTP_401_UNAUTHORIZED


class TokenRevoked(DomainError):
    code = "token_revoked"
    status_code = status.HTTP_401_UNAUTHORIZED


class Forbidden(DomainError):
    code = "forbidden"
    status_code = status.HTTP_403_FORBIDDEN


class NotFound(DomainError):
    code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND


class TooManyRequests(DomainError):
    code = "rate_limited"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )
