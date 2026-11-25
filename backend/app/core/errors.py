from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import StaleDataError
from starlette.exceptions import HTTPException

from pydantic import BaseModel
from .problem import Problem


class ErrorDetail(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


API_ERRORS = {
    status: {"model": ErrorResponse} for status in (401, 403, 404, 409, 422, 500, 503)
}


def install_errors(app: FastAPI):
    def response(status, message):
        return JSONResponse({"error": {"message": message}}, status_code=status)

    @app.exception_handler(Problem)
    def business(_, exc):
        return response(exc.status, str(exc))

    @app.exception_handler(HTTPException)
    def http(_, exc):
        return response(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    def invalid(_, exc):
        errors = [f"{'.'.join(map(str, e['loc']))} {e['msg']}" for e in exc.errors()]
        return response(422, " | ".join(errors))

    @app.exception_handler(IntegrityError)
    @app.exception_handler(StaleDataError)
    def conflict(_, exc):
        return response(
            409,
            "A record conflicts with existing data or has changed. Refresh and retry.",
        )

    @app.exception_handler(OperationalError)
    def unavailable(_, exc):
        return response(503, "Database temporarily unavailable. Refresh and retry.")

    @app.exception_handler(Exception)
    def unexpected(_, exc):
        return response(500, "An unexpected server error occurred.")
