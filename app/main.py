from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base, vault_engine, VaultBase

from app.api.v1.auth_router import router as auth_api_router
from app.api.v1.webhook_router import router as webhook_api_router
from app.api.v1.course_router import router as course_api_router
from app.api.v1.admin_router import router as admin_api_router
from app.api.v1.telemetry_router import router as telemetry_api_router
from app.api.v1.dashboard_router import router as dashboard_api_router
from app.api.v1.stream_router import router as stream_api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with vault_engine.begin() as conn:
        await conn.run_sync(VaultBase.metadata.create_all)

    yield


app = FastAPI(title="Nabegheha DRM API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://panel.devstorage.site",
        "https://api.devstorage.site",
        "http://localhost",
        "http://localhost:8080",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    """Health check endpoint"""
    return {"status": "ok", "service": "Nabegheha Secure Core is running"}


app.include_router(auth_api_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(webhook_api_router, prefix="/api/v1/webhook", tags=["Webhooks"])
app.include_router(course_api_router, prefix="/api/v1/course", tags=["Courses"])
app.include_router(admin_api_router, prefix="/api/v1/admin", tags=["Admin Panel"])
app.include_router(telemetry_api_router, prefix="/api/v1/telemetry", tags=["Telemetry"])
app.include_router(
    dashboard_api_router, prefix="/api/v1/dashboard", tags=["Dashboard Monitor"]
)
app.include_router(stream_api_router, prefix="/drm", tags=["Secure Streaming"])
