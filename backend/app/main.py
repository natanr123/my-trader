import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config.app_settings import app_settings


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if app_settings.SENTRY_DSN and app_settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(app_settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=app_settings.PROJECT_NAME,
    openapi_url=f"{app_settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if app_settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=app_settings.API_V1_STR)
