from .admin import router as admin_router
from .auth import router as auth_router
from .banner_messages import router as banner_messages_router
from .events import router as events_router
from .users import router as users_router
from .carousel import router as carousel_router
from .contact import router as contact_router
from .faq import router as faq_router
from .membership_options import router as membership_options_router
from .partners import router as partners_router
from .photos import router as photos_router
from .scholarship_recipients import router as scholarship_recipients_router

__all__ = ["auth_router", "events_router", "users_router", "banner_messages_router", "admin_router", "carousel_router", "contact_router", "faq_router", "membership_options_router", "partners_router", "photos_router", "scholarship_recipients_router"]
