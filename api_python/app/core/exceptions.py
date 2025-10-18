from typing import Optional


class AppException(Exception):
    """Base class for application-specific exceptions.

    Attributes:
        message: human-readable message
        status_code: HTTP status code to return (optional, default 400)
    """

    def __init__(self, message: str, status_code: int = 400, detail: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}

    def to_dict(self):
        payload = {"detail": self.message}
        if self.detail:
            payload["meta"] = self.detail
        return payload


class DownloadError(AppException):
    """Raised when audio download or postprocessing fails."""

    def __init__(self, message: str, status_code: int = 500, detail: Optional[dict] = None):
        super().__init__(message=message, status_code=status_code, detail=detail)
