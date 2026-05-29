from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine, Base
from app.api.v1.auth_router import router as auth_api_router
from app.api.v1.webhook_router import router as webhook_api_router
from app.api.v1.course_router import router as course_api_router
from app.api.v1.admin_router import router as admin_api_router
from app.api.v1.telemetry_router import router as telemetry_api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="DRM Microservice", version="1.0.0", lifespan=lifespan)

app.include_router(auth_api_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(webhook_api_router, prefix="/api/v1/webhook", tags=["Webhooks"])
app.include_router(course_api_router, prefix="/api/v1/course", tags=["Courses"])
app.include_router(admin_api_router, prefix="/api/v1/admin", tags=["Admin Panel"])
app.include_router(telemetry_api_router, prefix="/api/v1/telemetry", tags=["Telemetry"])