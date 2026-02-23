from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from core.config import settings
from routers import admin_router, auth_router, banner_messages_router, events_router, users_router, photos, carousel, partners, contact, faq, scholarship_recipients

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
app.include_router(photos.router)
app.include_router(carousel.router)
app.include_router(partners.router)
app.include_router(contact.router)
app.include_router(faq.router)
app.include_router(scholarship_recipients.router)

@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
