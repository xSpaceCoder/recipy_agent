import asyncio
import logging

from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


async def _fetch_page(url: str) -> str:
    strategies = [
        ("curl_cffi (Chrome impersonation)", _fetch_curl_cffi),
        ("cloudscraper (JS challenge solver)", _fetch_cloudscraper),
        ("httpx (plain HTTP)", _fetch_httpx),
    ]

    for name, fetch_fn in strategies:
        try:
            text = await fetch_fn(url)
            if _is_blocked(text):
                logger.info("%s returned a challenge/block page", name)
                continue
            return text
        except Exception as e:
            logger.info("%s failed with: %s", name, e)
            continue

    raise RuntimeError(
        "Failed to fetch URL with all available strategies. "
        "The site may be blocking automated requests."
    )


async def _fetch_page_for_images(url: str) -> str:
    strategies = [
        ("curl_cffi (Chrome impersonation)", _fetch_curl_cffi),
        ("cloudscraper (JS challenge solver)", _fetch_cloudscraper),
        ("httpx (plain HTTP)", _fetch_httpx),
    ]

    for name, fetch_fn in strategies:
        try:
            text = await fetch_fn(url)
            if _is_blocked(text):
                logger.info("%s returned a challenge/block page for images", name)
                continue
            return text
        except Exception as e:
            logger.info("%s failed for images with: %s", name, e)
            continue

    return None


def _is_blocked(html: str) -> bool:
    indicators = [
        "Zeig uns, dass du ein Mensch bist",
        "Enable JavaScript and cookies to continue",
        "Please enable JavaScript",
        "Just a moment...",
        "Checking your browser",
        "__cf_chl_opt",
        "_cf_chl_opt",
        "Attention Required",
        "Cloudflare",
    ]
    return any(i in html for i in indicators)


async def _fetch_curl_cffi(url: str) -> str:
    from curl_cffi import requests

    loop = asyncio.get_event_loop()
    r = await loop.run_in_executor(
        None,
        lambda: requests.get(url, impersonate="chrome120", timeout=20),
    )
    r.raise_for_status()
    return r.text


async def _fetch_cloudscraper(url: str) -> str:
    import cloudscraper

    loop = asyncio.get_event_loop()
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "desktop": True,
        }
    )
    r = await loop.run_in_executor(
        None, lambda: scraper.get(url, timeout=20)
    )
    r.raise_for_status()
    return r.text


async def _fetch_httpx(url: str) -> str:
    import httpx

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
    return r.text


async def scrape_webpage(url: str) -> str:
    html = await _fetch_page(url)
    soup = BeautifulSoup(html, "html.parser")

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
    html = await _fetch_page_for_images(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

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
