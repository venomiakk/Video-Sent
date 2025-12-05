from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import AppException
import logging

logger = logging.getLogger(__name__)

async def app_exception_handler(request: Request, exc: AppException):
    """Obsługa naszych własnych wyjątków (AppException, DownloadError)"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Obsługa błędów walidacji Pydantic (np. brakujące pole, zły typ)"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"]) if error["loc"] else "body"
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "meta": {"errors": errors}
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Obsługa standardowych błędów HTTP (404, 401, 403)"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Obsługa nieoczekiwanych błędów (500 Internal Server Error)"""
    logger.error(f"Global error occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "meta": {"message": "An unexpected error occurred. Please contact support."}
        }
    )