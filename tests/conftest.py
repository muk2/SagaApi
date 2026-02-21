from __future__ import annotations

import importlib.util
import os
import sys
import types

import pytest

# Set DATABASE_URL before any application imports that may trigger Settings()
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

# ---------------------------------------------------------------------------
# Bootstrap services.email_service without triggering the circular import
# in services/__init__.py -> auth_service -> core -> dependencies -> auth_service
# ---------------------------------------------------------------------------
_SRC_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "src")

# Insert a lightweight `services` package stub so Python can resolve
# `services.email_service` without executing the real __init__.py
if "services" not in sys.modules:
    _pkg = types.ModuleType("services")
    _pkg.__path__ = [os.path.join(_SRC_DIR, "services")]
    _pkg.__package__ = "services"
    sys.modules["services"] = _pkg

if "services.email_service" not in sys.modules:
    _spec = importlib.util.spec_from_file_location(
        "services.email_service",
        os.path.join(_SRC_DIR, "services", "email_service.py"),
    )
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["services.email_service"] = _mod
    _spec.loader.exec_module(_mod)


from services.email_service import EmailService  # noqa: E402


@pytest.fixture
def email_service() -> EmailService:
    """Provide a fresh EmailService instance for each test."""
    return EmailService()
