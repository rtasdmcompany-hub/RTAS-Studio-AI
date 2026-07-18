"""Typed access-control errors mapped to HTTP status codes."""

from __future__ import annotations


class AccessError(Exception):
    """Base access-control error with HTTP status."""

    def __init__(self, message: str, *, status_code: int = 403, code: str = "forbidden") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code

    def to_dict(self) -> dict:
        return {
            "ok": False,
            "error": self.code,
            "detail": self.message,
            "statusCode": self.status_code,
        }


class UnauthorizedError(AccessError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, status_code=401, code="unauthorized")


class ForbiddenError(AccessError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=403, code="forbidden")


class NotFoundError(AccessError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message, status_code=404, code="not_found")


class SessionInvalidError(UnauthorizedError):
    def __init__(self, message: str = "Session invalid or expired") -> None:
        super().__init__(message)
        self.code = "session_invalid"
