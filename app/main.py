from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base, vault_engine, VaultBase

from app.api.v1.webhooks.woocommerce_webhook import router as woocommerce_router

# Client-facing routers (end users of the secure player)
from app.api.v1.client.auth import router as client_auth_router
from app.api.v1.client.course import router as client_course_router
from app.api.v1.client.stream import router as client_stream_router
from app.api.v1.client.telemetry import router as client_telemetry_router

# Admin-facing routers (secure_admin panel)
from app.api.v1.admin.auth import router as admin_auth_router
from app.api.v1.admin.course import router as admin_course_router
from app.api.v1.admin.panel import router as admin_panel_router
from app.api.v1.admin.dashboard import router as admin_dashboard_router
from app.api.v1.admin.user import router as admin_user_router


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


app.include_router(woocommerce_router, prefix="/api/v1")

# --- Client routes (end-user secure player) ---
app.include_router(
    client_auth_router, prefix="/api/v1/client/auth", tags=["Client - Authentication"]
)
app.include_router(
    client_course_router, prefix="/api/v1/client/course", tags=["Client - Courses"]
)
app.include_router(
    client_stream_router, prefix="/drm", tags=["Client - Secure Streaming"]
)
app.include_router(
    client_telemetry_router,
    prefix="/api/v1/client/telemetry",
    tags=["Client - Telemetry"],
)

# --- Admin routes (secure_admin panel) ---
app.include_router(
    admin_auth_router, prefix="/api/v1/admin/auth", tags=["Admin - Authentication"]
)
app.include_router(
    admin_course_router, prefix="/api/v1/admin/course", tags=["Admin - Courses"]
)
app.include_router(admin_panel_router, prefix="/api/v1/admin", tags=["Admin - Panel"])
app.include_router(
    admin_dashboard_router, prefix="/api/v1/admin/dashboard", tags=["Admin - Dashboard"]
)
app.include_router(
    admin_user_router, prefix="/api/v1/admin/user", tags=["Admin - Users"]
)
