from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import AdminUser
from models.news_item import NewsItem
from schemas.news_item import (
    FetchNewsMetadataRequest,
    FetchNewsMetadataResponse,
    NewsItemCreate,
    NewsItemListResponse,
    NewsItemResponse,
    NewsItemUpdate,
)

router = APIRouter(prefix="/api", tags=["News"])

_FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SagaGolfBot/1.0; +https://sagagolf.org)"
}


def _meta_content(soup: BeautifulSoup, *, prop: Optional[str] = None, name: Optional[str] = None) -> Optional[str]:
    attrs = {"property": prop} if prop else {"name": name}
    tag = soup.find("meta", attrs=attrs)
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


# ===================================================================
# PUBLIC NEWS ENDPOINTS
# ===================================================================

@router.get("/news", response_model=NewsItemListResponse)
def get_news_items(db: Session = Depends(get_db)):
    """Get all news items ordered by display_order. Public endpoint."""
    items = db.query(NewsItem).order_by(NewsItem.display_order).all()
    return NewsItemListResponse(news_items=items)


# ===================================================================
# ADMIN NEWS ENDPOINTS (require admin authentication)
# ===================================================================

@router.get("/admin/news", response_model=NewsItemListResponse)
def admin_get_news_items(admin_user: AdminUser, db: Session = Depends(get_db)):
    items = db.query(NewsItem).order_by(NewsItem.display_order).all()
    return NewsItemListResponse(news_items=items)


@router.post("/admin/news/fetch-metadata", response_model=FetchNewsMetadataResponse)
def fetch_news_metadata(data: FetchNewsMetadataRequest, admin_user: AdminUser):
    """
    Best-effort scrape of a news article URL for its title, description and
    a representative image, so the admin doesn't have to type them by hand.
    Returns whatever fields it could find — the admin fills in the rest.
    """
    parsed = urlparse(data.url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must start with http:// or https://",
        )

    try:
        resp = requests.get(data.url, headers=_FETCH_HEADERS, timeout=8)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch the page: {exc}",
        )

    soup = BeautifulSoup(resp.text, "lxml")

    title = (
        _meta_content(soup, prop="og:title")
        or _meta_content(soup, name="twitter:title")
        or (soup.title.string.strip() if soup.title and soup.title.string else None)
    )

    description = (
        _meta_content(soup, prop="og:description")
        or _meta_content(soup, name="twitter:description")
        or _meta_content(soup, name="description")
    )

    image_url = _meta_content(soup, prop="og:image") or _meta_content(soup, name="twitter:image")
    if image_url:
        image_url = urljoin(data.url, image_url)

    site_name = _meta_content(soup, prop="og:site_name")
    if not site_name:
        # Fall back to the domain, e.g. "www.nj.com" -> "nj.com"
        host = urlparse(data.url).netloc
        site_name = host[4:] if host.startswith("www.") else host or None

    return FetchNewsMetadataResponse(
        title=title, description=description, image_url=image_url, site_name=site_name
    )


@router.post("/admin/news", response_model=NewsItemResponse, status_code=status.HTTP_201_CREATED)
def create_news_item(data: NewsItemCreate, admin_user: AdminUser, db: Session = Depends(get_db)):
    record = NewsItem(
        title=data.title,
        url=data.url,
        site_name=data.site_name,
        thumbnail_url=data.thumbnail_url,
        description=data.description,
        display_order=data.display_order,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/admin/news/{news_id}", response_model=NewsItemResponse)
def update_news_item(news_id: int, data: NewsItemUpdate, admin_user: AdminUser, db: Session = Depends(get_db)):
    record = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/admin/news/{news_id}")
def delete_news_item(news_id: int, admin_user: AdminUser, db: Session = Depends(get_db)):
    record = db.query(NewsItem).filter(NewsItem.id == news_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found")

    db.delete(record)
    db.commit()
    return {"message": "News item deleted successfully", "id": news_id}
