import asyncio
import logging

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
    try:
        result = await loop.run_in_executor(
            None, lambda: client.recipe_search(search_term=search_term)
        )
    except Exception as e:
        logger.error("REWE recipe search failed for %r: %s", search_term, e)
        raise

    recipes = result.get("recipes", [])
    return [
        {
            "id": r["id"],
            "title": r.get("title", ""),
            "detailUrl": r.get("detailUrl", ""),
            "image_url": (r.get("imageUrls") or [None])[0],
        }
        for r in recipes
    ]


async def fetch_rewe_recipe_by_id(recipe_id: str) -> dict:
    client = _get_client()
    if client is None:
        raise RuntimeError("REWE API not initialized. Set REWE_CERT_PATH and REWE_KEY_PATH.")

    loop = asyncio.get_event_loop()
    try:
        recipe = await loop.run_in_executor(
            None, lambda: client.get_recipe_details(recipe_id)
        )
    except Exception as e:
        logger.error("REWE recipe detail fetch failed for id %r: %s", recipe_id, e)
        raise

    if not recipe or not recipe.get("id"):
        raise RuntimeError("Failed to fetch recipe details")

    ingredients = [
        {
            "name": item.get("name", ""),
            "quantity": _format_quantity(item.get("quantity")),
            "unit": item.get("unit") or "",
        }
        for item in recipe.get("ingredients", [])
    ]

    instructions = [
        step.get("description", "")
        for step in recipe.get("preparation", {}).get("steps", [])
    ]

    image_urls = recipe.get("imageUrls") or []
    image_url = image_urls[0].get("urls", {}).get("default") if image_urls else None

    return {
        "title": recipe.get("title", ""),
        "description": "",
        "ingredients": ingredients,
        "instructions": instructions,
        "servings": recipe.get("serving", {}).get("quantity") or None,
        "prep_time_minutes": recipe.get("timePreparation"),
        "cook_time_minutes": recipe.get("timeCooking"),
        "bake_time_minutes": None,
        "chill_time_minutes": None,
        "freeze_time_minutes": None,
        "tags": [t.lower() for t in recipe.get("tags", [])],
        "category": None,
        "season": [],
        "image_url": image_url,
        "source_url": "",
        "source_type": "link",
    }


def _format_quantity(q) -> str:
    if q is None:
        return ""
    if isinstance(q, (int, float)):
        if q == int(q):
            return str(int(q))
        return str(q)
    return str(q)
