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
        "is_vegetarian": True,
        "source_accessed_at": "2024-01-01T00:00:00",
        "tags": ["vegetarian"],
        "category": "dinner",
        "season": ["all"],
        "visibility": "public",
        "source_url": "https://example.com/recipe",
        "source_type": "link",
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
    assert "source_accessed_at" not in inserted


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


def _make_mock_rewe_recipe():
    return {
        "title": "Blechkuchen mit Äpfeln",
        "description": "",
        "ingredients": [{"name": "Milch", "quantity": "250", "unit": "ml"}],
        "instructions": ["Teig kneten.", "Backen."],
        "servings": 20,
        "prep_time_minutes": 20,
        "cook_time_minutes": 45,
        "bake_time_minutes": None,
        "chill_time_minutes": None,
        "freeze_time_minutes": None,
        "tags": ["backen", "kuchen"],
        "category": None,
        "season": [],
        "image_url": "https://c.rewe-static.de/00000005/1/00000005.png",
        "source_url": "",
        "source_type": "link",
    }


def _configured_rewe_settings():
    settings = MagicMock()
    settings.rewe_cert_path = "/secrets/rewe-cert/latest"
    settings.rewe_key_path = "/secrets/rewe-key/latest"
    return settings


def test_rewe_search_returns_400_when_certs_not_configured(client):
    client.app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@test.com"}

    unconfigured = MagicMock()
    unconfigured.rewe_cert_path = ""
    unconfigured.rewe_key_path = ""

    with patch("app.routers.ingestion.get_settings", return_value=unconfigured):
        response = client.post("/api/ingest/rewe/search", json={"search_term": "Nudeln"})

    assert response.status_code == 400
    assert "REWE_CERT_PATH" in response.json()["detail"]


def test_rewe_search_returns_500_when_client_init_fails(client):
    client.app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@test.com"}

    with (
        patch("app.routers.ingestion.get_settings", return_value=_configured_rewe_settings()),
        patch("app.routers.ingestion.init_rewerse", return_value=False),
    ):
        response = client.post("/api/ingest/rewe/search", json={"search_term": "Nudeln"})

    assert response.status_code == 500


def test_rewe_search_returns_400_on_search_failure(client):
    client.app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@test.com"}

    with (
        patch("app.routers.ingestion.get_settings", return_value=_configured_rewe_settings()),
        patch("app.routers.ingestion.init_rewerse", return_value=True),
        patch("app.routers.ingestion.search_rewe_recipes", side_effect=Exception("REWE 403")),
    ):
        response = client.post("/api/ingest/rewe/search", json={"search_term": "Nudeln"})

    assert response.status_code == 400
    assert "REWE 403" in response.json()["detail"]


def test_rewe_confirm_saves_recipe_with_ai_classified_metadata(client):
    recipe = _make_mock_rewe_recipe()
    saved = _make_mock_saved_record()
    classified = {"category": "cake", "season": ["autumn"], "tags": ["vegetarian", "cozy"], "is_vegetarian": True}

    client.app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@test.com"}

    with (
        patch("app.routers.ingestion.get_settings", return_value=_configured_rewe_settings()),
        patch("app.routers.ingestion.init_rewerse", return_value=True),
        patch("app.routers.ingestion.fetch_rewe_recipe_by_id", return_value=recipe),
        patch("app.routers.ingestion.classify_recipe_metadata", return_value=classified),
        patch("app.routers.ingestion._get_supabase") as mock_get_sb,
    ):
        mock_sb = MagicMock()
        mock_sb.table.return_value.insert.return_value.execute.return_value.data = [saved]
        mock_get_sb.return_value = mock_sb

        response = client.post(
            "/api/ingest/rewe/confirm",
            json={"recipe_id": "blt555", "detail_url": "https://www.rewe.de/rezepte/blechkuchen-mit-aepfeln/"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["saved"] is True
    assert data["category"] == "cake"
    assert data["season"] == ["autumn"]
    assert set(data["tags"]) == {"backen", "kuchen", "vegetarian", "cozy"}
    assert data["source_url"] == "https://www.rewe.de/rezepte/blechkuchen-mit-aepfeln/"
    assert data["source_type"] == "link"


def test_rewe_confirm_falls_back_to_raw_mapping_when_ai_fails(client):
    recipe = _make_mock_rewe_recipe()
    saved = _make_mock_saved_record()

    client.app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@test.com"}

    with (
        patch("app.routers.ingestion.get_settings", return_value=_configured_rewe_settings()),
        patch("app.routers.ingestion.init_rewerse", return_value=True),
        patch("app.routers.ingestion.fetch_rewe_recipe_by_id", return_value=recipe),
        patch("app.routers.ingestion.classify_recipe_metadata", side_effect=Exception("Gemini error")),
        patch("app.routers.ingestion._get_supabase") as mock_get_sb,
    ):
        mock_sb = MagicMock()
        mock_sb.table.return_value.insert.return_value.execute.return_value.data = [saved]
        mock_get_sb.return_value = mock_sb

        response = client.post(
            "/api/ingest/rewe/confirm",
            json={"recipe_id": "blt555", "detail_url": "https://www.rewe.de/rezepte/blechkuchen-mit-aepfeln/"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["category"] is None
    assert data["tags"] == ["backen", "kuchen"]


def test_rewe_confirm_returns_400_on_fetch_failure(client):
    client.app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@test.com"}

    with (
        patch("app.routers.ingestion.get_settings", return_value=_configured_rewe_settings()),
        patch("app.routers.ingestion.init_rewerse", return_value=True),
        patch("app.routers.ingestion.fetch_rewe_recipe_by_id", side_effect=Exception("recipe not found")),
    ):
        response = client.post(
            "/api/ingest/rewe/confirm",
            json={"recipe_id": "missing", "detail_url": "https://www.rewe.de/rezepte/missing/"},
        )

    assert response.status_code == 400
    assert "recipe not found" in response.json()["detail"]
