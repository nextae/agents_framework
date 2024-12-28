from fastapi import HTTPException, Request, Response
from fastapi.exception_handlers import http_exception_handler

from app.api.errors import ConflictError, NotFoundError


async def not_found_error_handler(request: Request, exc: NotFoundError) -> Response:
    return await http_exception_handler(
        request, HTTPException(status_code=404, detail=str(exc))
    )


async def conflict_error_handler(request: Request, exc: ConflictError) -> Response:
    return await http_exception_handler(
        request, HTTPException(status_code=409, detail=str(exc))
    )
