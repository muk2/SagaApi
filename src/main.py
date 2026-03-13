from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from core.config import settings

# Path to React build output
REACT_BUILD_DIR = Path(__file__).resolve().parent.parent.parent / "SagaFe" / "sagafe" / "build"
from routers import (
    admin_router,
    auth_router,
    banner_messages_router,
    carousel_router,
    contact_router,
    events_router,
    faq_router,
    membership_options_router,
    partners_router,
    photos_router,
    scholarship_recipients_router,
    users_router,
    standings_router,
    past_champions_router
)
from routers.registrations import router as registrations_router

os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="Saga Golf API",
    description="API for Saga Golf non-profit organization",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router)
app.include_router(events_router)
app.include_router(users_router)
app.include_router(banner_messages_router)
app.include_router(admin_router)
app.include_router(photos_router)
app.include_router(carousel_router)
app.include_router(partners_router)
app.include_router(contact_router)
app.include_router(faq_router)
app.include_router(scholarship_recipients_router)
app.include_router(membership_options_router)
app.include_router(standings_router)
app.include_router(registrations_router)
app.include_router(past_champions_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# Apple Pay domain verification file
APPLE_PAY_VERIFICATION_FILE = Path(__file__).resolve().parent.parent / ".well-known" / "apple-developer-merchantid-domain-association"

@app.get("/.well-known/apple-developer-merchantid-domain-association")
def apple_pay_domain_verification():
    """Serve Apple Pay domain verification file."""
    if APPLE_PAY_VERIFICATION_FILE.is_file():
        return FileResponse(str(APPLE_PAY_VERIFICATION_FILE), media_type="text/plain")
    return {"error": "Verification file not found"}


# Serve React frontend build (for single-URL dev tunnels like ngrok)
if REACT_BUILD_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(REACT_BUILD_DIR / "static")), name="react-static")

    from starlette.responses import Response

    @app.middleware("http")
    async def serve_react(request: Request, call_next):
        """Serve React build for non-API routes."""
        response = await call_next(request)

        # If the API returned 404 and it's not an /api/, /auth/, /uploads/, or /health path,
        # serve React index.html for client-side routing
        path = request.url.path
        is_api = path.startswith(('/api/', '/auth/', '/uploads/', '/health', '/docs', '/openapi.json', '/redoc'))

        if response.status_code == 404 and not is_api:
            # Try to serve exact file from build dir
            file_path = REACT_BUILD_DIR / path.lstrip('/')
            if file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(REACT_BUILD_DIR / "index.html"))

        return response