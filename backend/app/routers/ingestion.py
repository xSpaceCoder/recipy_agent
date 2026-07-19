import logging
import re
import uuid
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from supabase import create_client
from app.config import get_settings
from app.auth import get_current_user
from app.services.ai_parser import (
    parse_recipe_from_text,
    parse_recipe_from_images,
    parse_recipe_from_video,
    select_dish_image_from_photos,
)
from app.services.scraper import scrape_webpage, extract_image_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


def _get_supabase():
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


class UrlRequest(BaseModel):
    url: str


@router.post("/url")
async def ingest_from_url(request: UrlRequest, user: dict = Depends(get_current_user)):
    try:
        content = await scrape_webpage(request.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    if not content.strip():
        raise HTTPException(status_code=400, detail="No content found at URL")

    try:
        recipe = parse_recipe_from_text(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"AI parsing failed: {e}")

    if "error" in recipe:
        raise HTTPException(status_code=422, detail=recipe["error"])

    try:
        image_url = await extract_image_url(request.url)
        if image_url:
            recipe["image_url"] = image_url
    except Exception:
        pass

    recipe["source_url"] = request.url
    recipe["source_type"] = "link"
    recipe["source_accessed_at"] = _now_iso()
    return recipe


@router.post("/youtube")
async def ingest_from_youtube(request: UrlRequest, user: dict = Depends(get_current_user)):
    logger.info(f"YouTube ingestion request for: {request.url}")

    try:
        recipe = parse_recipe_from_video(request.url)
    except Exception as e:
        logger.error(f"AI video parsing failed: {e}")
        raise HTTPException(status_code=422, detail=f"AI parsing failed: {e}")

    if "error" in recipe:
        logger.warning(f"AI returned error: {recipe['error']}")
        raise HTTPException(status_code=422, detail=recipe["error"])

    video_id = _extract_youtube_video_id(request.url)
    if video_id:
        candidates = await _fetch_youtube_thumbnails(video_id)
        if candidates:
            try:
                best_index = select_dish_image_from_photos(
                    recipe.get("title", ""), candidates
                )
                if best_index >= 0 and best_index < len(candidates):
                    recipe["image_url"] = candidates[best_index]["url"]
                else:
                    recipe["image_url"] = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            except Exception as e:
                logger.warning(f"AI image selection failed, using fallback: {e}")
                recipe["image_url"] = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        else:
            recipe["image_url"] = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    recipe["source_url"] = request.url
    recipe["source_type"] = "video"
    recipe["source_accessed_at"] = _now_iso()
    logger.info(f"Successfully parsed recipe: {recipe.get('title', 'unknown')}")
    return recipe


@router.post("/image")
async def ingest_from_image(files: list[UploadFile] = File(...), user: dict = Depends(get_current_user)):
    if not files:
        raise HTTPException(status_code=400, detail="No images provided")

    images = []
    for f in files:
        if not f.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File {f.filename} is not an image")
        data = await f.read()
        images.append({"mime_type": f.content_type, "data": data, "filename": f.filename})

    try:
        recipe = parse_recipe_from_images(images)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"AI parsing failed: {e}")

    if "error" in recipe:
        raise HTTPException(status_code=422, detail=recipe["error"])

    source_image_urls = _upload_source_images(images)

    recipe["source_type"] = "image"
    recipe["source_accessed_at"] = _now_iso()
    recipe["source_image_urls"] = source_image_urls
    if source_image_urls:
        hero_index = recipe.pop("hero_image_index", None)
        if isinstance(hero_index, int) and 0 <= hero_index < len(source_image_urls):
            recipe["image_url"] = source_image_urls[hero_index]
        else:
            recipe["image_url"] = source_image_urls[0]
    return recipe


_YOUTUBE_ID_PATTERNS = [
    r'youtube\.com/shorts/([a-zA-Z0-9_-]+)',
    r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
    r'youtu\.be/([a-zA-Z0-9_-]+)',
]


def _extract_youtube_video_id(url: str) -> str | None:
    for pattern in _YOUTUBE_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


_THUMBNAIL_QUALITIES = [
    ("maxresdefault", "maxresdefault.jpg"),
    ("sddefault", "sddefault.jpg"),
    ("hqdefault", "hqdefault.jpg"),
    ("mqdefault", "mqdefault.jpg"),
]

_STORYBOARD_FRAMES = [(f"frame_{i}", f"{i}.jpg") for i in range(4)]


async def _fetch_youtube_thumbnails(video_id: str) -> list[dict]:
    base = f"https://img.youtube.com/vi/{video_id}"
    candidates = []
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        for name, filename in _THUMBNAIL_QUALITIES + _STORYBOARD_FRAMES:
            url = f"{base}/{filename}"
            try:
                response = await client.get(url)
                if response.status_code == 200 and response.headers.get("content-type", "").startswith("image/"):
                    candidates.append({
                        "name": name,
                        "url": url,
                        "mime_type": response.headers["content-type"],
                        "data": response.content,
                    })
            except Exception:
                continue
    return candidates


def _upload_source_images(images: list[dict]) -> list[str]:
    sb = _get_supabase()
    settings = get_settings()
    urls = []
    for img in images:
        ext = img["mime_type"].split("/")[-1]
        path = f"{uuid.uuid4()}.{ext}"
        sb.storage.from_("source-images").upload(
            path, img["data"], {"content-type": img["mime_type"]}
        )
        public_url = f"{settings.supabase_url}/storage/v1/object/public/source-images/{path}"
        urls.append(public_url)
    return urls
