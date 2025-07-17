import logging
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.responses import RedirectResponse, Response

from app.core.config import settings
from app.api.v1 import planner_days, planner_agendas, auth

# Ensure logs directory exists
logs_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=settings.LOGGING_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(logs_dir, "app.log"), mode="a", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Application starting in {'development' if settings.IS_DEV else 'production'} mode")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(planner_days.router, prefix=f"{settings.API_V1_STR}/planner/days", tags=["planner_days"])
app.include_router(planner_agendas.router, prefix=f"{settings.API_V1_STR}/planner/agendas", tags=["planner_agendas"])

@app.get("/")
def root():
    if settings.ROOT_URL_REDIRECT:
        return RedirectResponse(url=settings.ROOT_URL_REDIRECT)
    return Response(content='OK', status_code=status.HTTP_200_OK)

@app.get("/health/")
def health():
    return Response(content="OK", status_code=status.HTTP_200_OK)
