import asyncio
import logging
import re

logger = logging.getLogger(__name__)

_client = None
_client_lock = asyncio.Lock()


def _get_client():
    global _client
    return _client


async def init_rewerse(cert_path: str, key_path: str) -> bool:
    global _client
    async with _client_lock:
        if _client is not None:
            return True
        loop = asyncio.get_event_loop()

        def _init():
            from rewerse import Rewerse
            return Rewerse(cert=cert_path, key=key_path)

        try:
            _client = await loop.run_in_executor(None, _init)
            logger.info("REWE API client initialized")
            return True
        except Exception as e:
            logger.error("Failed to initialize REWE API client: %s", e)
            _client = None
            return False


async def search_rewe_recipes(search_term: str) -> list[dict]:
    client = _get_client()
    if client is None:
        raise RuntimeError("REWE API not initialized. Set REWE_CERT_PATH and REWE_KEY_PATH.")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, lambda: client.recipe_search(search_term=search_term)
    )

    recipes = result.get("recipes", [])
    return [
        {
            "id": r["id"],
            "title": r.get("title", ""),
            "detailUrl": r.get("detailUrl", ""),
        }
        for r in recipes
    ]


async def fetch_rewe_recipe_by_id(recipe_id: str) -> dict:
    client = _get_client()
    if client is None:
        raise RuntimeError("REWE API not initialized. Set REWE_CERT_PATH and REWE_KEY_PATH.")

    loop = asyncio.get_event_loop()
    details = await loop.run_in_executor(
        None, lambda: client.get_recipe_details(recipe_id)
    )

    recipe = details.get("recipe", {})
    if not recipe:
        raise RuntimeError("Failed to fetch recipe details")

    ingredients_raw = recipe.get("ingredients", {})
    ingredients = [
        {
            "name": item.get("name", ""),
            "quantity": _format_quantity(item.get("quantity", 0)),
            "unit": item.get("unit", ""),
        }
        for item in ingredients_raw.get("items", [])
    ]

    servings = ingredients_raw.get("portions", 0) or None
    total_minutes = _parse_duration(recipe.get("duration", ""))

    tags = []
    difficulty = recipe.get("difficultyDescription", "").lower()
    if difficulty:
        tags.append(difficulty)

    return {
        "title": recipe.get("title", ""),
        "description": "",
        "ingredients": ingredients,
        "instructions": recipe.get("steps", []),
        "servings": servings,
        "prep_time_minutes": total_minutes or None,
        "cook_time_minutes": None,
        "bake_time_minutes": None,
        "chill_time_minutes": None,
        "freeze_time_minutes": None,
        "tags": tags,
        "category": None,
        "season": [],
        "image_url": recipe.get("imageUrl") or None,
        "source_url": "",
        "source_type": "link",
    }


def _parse_duration(duration: str) -> int:
    if not duration:
        return 0
    total = 0
    h = re.search(r"(\d+)\s*(?:Std\.|Stunden|h)", duration)
    if h:
        total += int(h.group(1)) * 60
    m = re.search(r"(\d+)\s*(?:Min\.|Minuten|min|m)", duration)
    if m:
        total += int(m.group(1))
    return total


def _format_quantity(q) -> str:
    if q is None:
        return ""
    if isinstance(q, (int, float)):
        if q == int(q):
            return str(int(q))
        return str(q).replace(".", ",") if q == round(q, 1) else str(q)
    return str(q)
