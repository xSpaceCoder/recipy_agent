import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin


async def scrape_webpage(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Try to find recipe-specific content first
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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 1. og:image meta tag (most reliable for recipe sites)
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        return _absolutify(og_image["content"], url)

    # 2. Schema.org Recipe image
    recipe_el = soup.select_one('[itemtype*="Recipe"]')
    if recipe_el:
        img = recipe_el.find("img", src=True)
        if img:
            return _absolutify(img["src"], url)

    # 3. First large image in recipe-related content
    for selector in ['[class*="recipe"]', '[id*="recipe"]', "article"]:
        container = soup.select_one(selector)
        if container:
            img = container.find("img", src=True)
            if img:
                return _absolutify(img["src"], url)

    # 4. twitter:image
    twitter_img = soup.find("meta", attrs={"name": "twitter:image"})
    if twitter_img and twitter_img.get("content"):
        return _absolutify(twitter_img["content"], url)

    return None


def _absolutify(img_url: str, base_url: str) -> str:
    if img_url.startswith("http"):
        return img_url
    return urljoin(base_url, img_url)
