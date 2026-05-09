import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.services.ai_parser import parse_recipe_from_text, parse_recipe_from_images, parse_recipe_from_video
from app.services.scraper import scrape_webpage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


class UrlRequest(BaseModel):
    url: str


@router.post("/url")
async def ingest_from_url(request: UrlRequest):
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

    recipe["source_url"] = request.url
    recipe["source_type"] = "link"
    return recipe


@router.post("/youtube")
async def ingest_from_youtube(request: UrlRequest):
    logger.info(f"YouTube ingestion request for: {request.url}")

    try:
        recipe = parse_recipe_from_video(request.url)
    except Exception as e:
        logger.error(f"AI video parsing failed: {e}")
        raise HTTPException(status_code=422, detail=f"AI parsing failed: {e}")

    if "error" in recipe:
        logger.warning(f"AI returned error: {recipe['error']}")
        raise HTTPException(status_code=422, detail=recipe["error"])

    recipe["source_url"] = request.url
    recipe["source_type"] = "video"
    logger.info(f"Successfully parsed recipe: {recipe.get('title', 'unknown')}")
    return recipe


@router.post("/image")
async def ingest_from_image(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No images provided")

    images = []
    for f in files:
        if not f.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File {f.filename} is not an image")
        data = await f.read()
        images.append({"mime_type": f.content_type, "data": data})

    try:
        recipe = parse_recipe_from_images(images)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"AI parsing failed: {e}")

    if "error" in recipe:
        raise HTTPException(status_code=422, detail=recipe["error"])

    recipe["source_type"] = "image"
    return recipe
