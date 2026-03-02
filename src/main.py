from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from core.config import settings
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
    standings_router
)

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

@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
