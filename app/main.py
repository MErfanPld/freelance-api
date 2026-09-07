from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.middleware.security import SecurityHeadersMiddleware


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Freelance Project Manager API",
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers
app.add_middleware(SecurityHeadersMiddleware)


# Application exceptions
@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": exc.data,
            "message": exc.message,
        },
    )


# FastAPI HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "success": False,
            "data": None,
            "message": str(exc.detail),
        },
    )


# Pydantic validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    errors = []

    for error in exc.errors():
        location = error.get("loc", [])
        message = error.get("msg", "Invalid value")

        field = None

        if len(location) > 1:
            field = ".".join(
                str(item)
                for item in location
                if item != "body"
            )

        errors.append(
            {
                "field": field,
                "message": message,
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": errors,
            "message": "Validation error",
        },
    )


# Unexpected errors
@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
):
    if settings.debug:
        print(
            f"Unhandled exception: "
            f"{type(exc).__name__}: {exc}"
        )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": "Internal server error",
        },
    )


app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "success": True,
        "data": {
            "name": settings.app_name,
            "version": settings.app_version,
        },
        "message": None,
    }