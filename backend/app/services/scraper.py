import asyncio
import logging
import cloudscraper
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

_scraper = None


def _get_scraper():
    global _scraper
    if _scraper is None:
        _scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True,
            }
        )
    return _scraper


async def scrape_webpage(url: str) -> str:
    loop = asyncio.get_event_loop()
    scraper = _get_scraper()

    try:
        response = await loop.run_in_executor(
            None, lambda: scraper.get(url, timeout=20.0)
        )
        response.raise_for_status()
    except Exception:
        logger.info("cloudscraper failed, falling back to httpx")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
            }
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
        except Exception as e:
            raise e

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    recipe_selectors = [
        '[itemtype*="Recipe"]',
        '[class*="recipe"]',
        '[id*="recipe"]',
        "article",
    ]
    for selector in recipe_selectors:
        element = soup.select_one(selector)
        if element and len(element.get_text(strip=True)) > 100:
            return element.get_text(separator="\n", strip=True)[:8000]

    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)[:8000]

    return soup.get_text(separator="\n", strip=True)[:8000]


async def extract_image_url(url: str) -> str | None:
    loop = asyncio.get_event_loop()
    scraper = _get_scraper()

    try:
        response = await loop.run_in_executor(
            None, lambda: scraper.get(url, timeout=20.0)
        )
        response.raise_for_status()
    except Exception:
        logger.info("cloudscraper failed for image extraction, falling back to httpx")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            }
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
        except Exception as e:
            raise e

    soup = BeautifulSoup(response.text, "html.parser")

    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        return _absolutify(og_image["content"], url)

    recipe_el = soup.select_one('[itemtype*="Recipe"]')
    if recipe_el:
        img = recipe_el.find("img", src=True)
        if img:
            return _absolutify(img["src"], url)

    for selector in ['[class*="recipe"]', '[id*="recipe"]', "article"]:
        container = soup.select_one(selector)
        if container:
            img = container.find("img", src=True)
            if img:
                return _absolutify(img["src"], url)

    twitter_img = soup.find("meta", attrs={"name": "twitter:image"})
    if twitter_img and twitter_img.get("content"):
        return _absolutify(twitter_img["content"], url)

    return None


def _absolutify(img_url: str, base_url: str) -> str:
    if img_url.startswith("http"):
        return img_url
    return urljoin(base_url, img_url)
