import asyncio
import pytest
from unittest.mock import MagicMock

from app.services import rewe_api

SAMPLE_SEARCH_RESULT = {
    "recipes": [
        {
            "id": "blt111",
            "title": "Nudeln mit Tomatensauce",
            "detailUrl": "https://www.rewe.de/rezepte/nudeln-mit-tomatensosse/",
            "imageUrls": ["https://c.rewe-static.de/thumb.png"],
        },
    ],
    "metadata": {"totalRecipeCount": 1},
}

SAMPLE_RECIPE_DETAILS = {
    "id": "blt555",
    "title": "Blechkuchen mit Äpfeln",
    "difficulty": 2,
    "serving": {"type": "pieces", "quantity": 20},
    "timeCooking": 45,
    "timePreparation": 20,
    "timeTotal": 75,
    "preparation": {"steps": [{"description": "Teig kneten."}, {"description": "Backen."}]},
    "imageUrls": [{"urls": {"default": "https://c.rewe-static.de/00000005/1/00000005.png"}}],
    "detailUrl": "blechkuchen-mit-aepfeln",
    "tags": ["Backen", "Kuchen", "Vegetarisch"],
    "ingredients": [
        {"quantity": 250.0, "unit": "ml", "name": "Milch", "displayName": "250 ml Milch"},
        {"quantity": 2.0, "unit": None, "name": "Eier", "displayName": "2 Eier"},
    ],
}


@pytest.fixture(autouse=True)
def reset_client():
    rewe_api._client = None
    yield
    rewe_api._client = None


def test_search_rewe_recipes_maps_fields():
    mock_client = MagicMock()
    mock_client.recipe_search.return_value = SAMPLE_SEARCH_RESULT
    rewe_api._client = mock_client

    results = asyncio.run(rewe_api.search_rewe_recipes("Nudeln"))

    assert results == [
        {
            "id": "blt111",
            "title": "Nudeln mit Tomatensauce",
            "detailUrl": "https://www.rewe.de/rezepte/nudeln-mit-tomatensosse/",
            "image_url": "https://c.rewe-static.de/thumb.png",
        }
    ]


def test_fetch_rewe_recipe_by_id_maps_fields():
    mock_client = MagicMock()
    mock_client.get_recipe_details.return_value = SAMPLE_RECIPE_DETAILS
    rewe_api._client = mock_client

    recipe = asyncio.run(rewe_api.fetch_rewe_recipe_by_id("blt555"))

    assert recipe["title"] == "Blechkuchen mit Äpfeln"
    assert recipe["servings"] == 20
    assert recipe["prep_time_minutes"] == 20
    assert recipe["cook_time_minutes"] == 45
    assert recipe["instructions"] == ["Teig kneten.", "Backen."]
    assert recipe["ingredients"] == [
        {"name": "Milch", "quantity": "250", "unit": "ml"},
        {"name": "Eier", "quantity": "2", "unit": ""},
    ]
    assert recipe["tags"] == ["backen", "kuchen", "vegetarisch"]
    assert recipe["image_url"] == "https://c.rewe-static.de/00000005/1/00000005.png"


def test_fetch_rewe_recipe_by_id_raises_on_empty_details():
    mock_client = MagicMock()
    mock_client.get_recipe_details.return_value = {}
    rewe_api._client = mock_client

    with pytest.raises(RuntimeError):
        asyncio.run(rewe_api.fetch_rewe_recipe_by_id("missing"))


def test_search_rewe_recipes_raises_when_not_initialized():
    with pytest.raises(RuntimeError):
        asyncio.run(rewe_api.search_rewe_recipes("Nudeln"))
