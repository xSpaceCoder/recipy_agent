### Task 2: Backend — Write tests for ingestion save

**Files:**
- Create: `backend/tests/test_ingestion.py`
- Modify: `backend/tests/conftest.py` (optional — add ingestion-specific fixture)

- [ ] **Step 1: Create test file with mocks**

Create `backend/tests/test_ingestion.py`:

```python
from unittest.mock import patch, MagicMock

from app.auth import get_current_user


def _make_mock_recipe():
    return {
        "title": "Test Recipe",
        "description": "A test",
        "ingredients": [{"name": "flour", "quantity": "200", "unit": "g"}],
        "instructions": ["Mix", "Bake"],
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "tags": ["vegetarian"],
        "category": "dinner",
        "season": ["all"],
        "visibility": "public",
        "source_url": "https://example.com/recipe",
        "source_type": "link",
        "is_vegetarian": True,
        "error": None,
    }


def _make_mock_saved_record():
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "title": "Test Recipe",
        "user_id": "user-123",
        "visibility": "private",
    }


def test_ingest_url_saves_to_supabase(client):
    """Verify /api/ingest/url calls save helper and returns saved recipe."""
    recipe = _make_mock_recipe()
    saved = _make_mock_saved_record()

    client.app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@test.com"}

    with (
        patch("app.routers.ingestion.scrape_webpage", return_value="<html>recipe</html>"),
        patch("app.routers.ingestion.parse_recipe_from_text", return_value=recipe),
        patch("app.routers.ingestion.extract_image_url", return_value=None),
        patch("app.routers.ingestion._get_supabase") as mock_get_sb,
    ):
        mock_sb = MagicMock()
        mock_sb.table.return_value.insert.return_value.execute.return_value.data = [saved]
        mock_get_sb.return_value = mock_sb

        response = client.post(
            "/api/ingest/url",
            json={"url": "https://example.com/recipe"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["saved"] is True
    assert data["id"] == saved["id"]
    assert data["title"] == "Test Recipe"

    insert_call = mock_sb.table.return_value.insert
    insert_call.assert_called_once()
    inserted = insert_call.call_args[0][0]
    assert inserted["user_id"] == "user-123"
    assert inserted["visibility"] == "private"
    assert "is_vegetarian" not in inserted
    assert "error" not in inserted


def test_ingest_url_returns_422_on_ai_failure(client):
    """Verify AI failure returns 422 and no save is attempted."""
    client.app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@test.com"}

    with (
        patch("app.routers.ingestion.scrape_webpage", return_value="<html>recipe</html>"),
        patch("app.routers.ingestion.parse_recipe_from_text", side_effect=Exception("AI error")),
    ):
        response = client.post(
            "/api/ingest/url",
            json={"url": "https://example.com/recipe"},
        )

    assert response.status_code == 422
    assert "AI error" in response.json()["detail"]


def test_ingest_url_returns_500_on_save_failure(client):
    """Verify Supabase save failure returns 500."""
    recipe = _make_mock_recipe()

    client.app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@test.com"}

    with (
        patch("app.routers.ingestion.scrape_webpage", return_value="<html>recipe</html>"),
        patch("app.routers.ingestion.parse_recipe_from_text", return_value=recipe),
        patch("app.routers.ingestion.extract_image_url", return_value=None),
        patch("app.routers.ingestion._get_supabase") as mock_get_sb,
    ):
        mock_sb = MagicMock()
        mock_sb.table.return_value.insert.side_effect = Exception("DB error")
        mock_get_sb.return_value = mock_sb

        response = client.post(
            "/api/ingest/url",
            json={"url": "https://example.com/recipe"},
        )

    assert response.status_code == 500
```

- [ ] **Step 2: Run tests to verify they pass

```bash
cd backend && .venv/Scripts/python -m pytest tests/test_ingestion.py -v
```

Expected: 3 tests pass.
