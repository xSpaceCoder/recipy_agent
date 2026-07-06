import os
import pytest
from unittest.mock import patch, MagicMock

# Set dummy env vars before importing app modules
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")
os.environ.setdefault("GOOGLE_AI_API_KEY", "test-key")

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client with mocked external dependencies."""
    with patch("app.database.get_supabase", return_value=MagicMock()):
        from app.main import app
        with TestClient(app) as c:
            yield c
