import httpx
from bs4 import BeautifulSoup


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
