# Auto-Save on Recipe Ingestion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Backend saves every parsed recipe to Supabase automatically after AI processing. Frontend preview becomes a confirmation step with "View in List" / "Discard" instead of "Save" / "Discard".

**Architecture:** Each ingestion endpoint (`/url`, `/youtube`, `/image`) calls a `_save_recipe_to_supabase` helper after AI parsing, before returning the response. The save uses the service role key and is scoped to the authenticated user. The frontend removes `handleSave`, adds a "Skip & Save" button during loading, and changes the preview to show "✓ Recipe saved" with "View in List" / "Discard" buttons.

**Tech Stack:** Python FastAPI, Supabase (service role key), Gemini AI parser, React (supabase-js client)

## Global Constraints

- All auto-saved recipes default to `visibility: "private"`
- Fields `is_vegetarian`, `error`, `hero_image_index`, `source_image_urls`, `source_accessed_at` are stripped before insert
- The save happens BEFORE the response is sent (so client disconnect still saves the recipe)
- No schema changes to the `recipes` table

---

### Task 1: Backend — Add save helper + update ingestion endpoints

**Files:**
- Modify: `backend/app/routers/ingestion.py`

**Interfaces:**
- Consumes: existing `_get_supabase()` helper, existing AI parser functions
- Produces: `_save_recipe_to_supabase(sb, recipe, user_id) -> dict`, modified endpoints

- [ ] **Step 1: Add `_save_recipe_to_supabase` helper**

Add after `_now_iso()` (around line 31):

```python
_SAVE_FIELDS = {
    "title", "description", "ingredients", "instructions",
    "servings", "prep_time_minutes", "cook_time_minutes",
    "bake_time_minutes", "chill_time_minutes", "freeze_time_minutes",
    "tags", "category", "season", "rating", "visibility",
    "image_url", "source_url", "source_type",
}


def _save_recipe_to_supabase(sb, recipe: dict, user_id: str) -> dict:
    data = {k: v for k, v in recipe.items() if k in _SAVE_FIELDS}
    data["user_id"] = user_id
    data.setdefault("visibility", "private")
    result = sb.table("recipes").insert(data).execute()
    return result.data[0]
```

- [ ] **Step 2: Update `/api/ingest/url` endpoint to save**

At the end of `ingest_from_url`, before `return recipe`, add:

```python
    try:
        sb = _get_supabase()
        saved = _save_recipe_to_supabase(sb, recipe, user["id"])
        recipe["id"] = saved["id"]
        recipe["saved"] = True
    except Exception as e:
        logger.error(f"Failed to save recipe: {e}")
        raise HTTPException(status_code=500, detail="Failed to save recipe")

    return recipe
```

- [ ] **Step 3: Update `/api/ingest/youtube` endpoint to save**

Same block as Step 2, inserted before the final `return recipe` in `ingest_from_youtube`.

- [ ] **Step 4: Update `/api/ingest/image` endpoint to save**

Same block as Step 2, inserted before the final `return recipe` in `ingest_from_image`.

- [ ] **Step 5: Run existing tests to verify nothing broke**

```bash
cd backend && .venv/Scripts/python -m pytest tests/ -v
```

Expected: `test_health_endpoint` passes.

---

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

- [ ] **Step 2: Run tests to verify they pass**

```bash
cd backend && .venv/Scripts/python -m pytest tests/test_ingestion.py -v
```

Expected: 3 tests pass.

---

### Task 3: Frontend — Update RecipeIngest component

**Files:**
- Modify: `frontend/src/components/RecipeIngest.jsx`
- Modify: `frontend/src/index.css` (add CSS for skip button and saved notice)

- [ ] **Step 1: Remove `handleSave` function**

Delete the `handleSave` function (lines 85-101 in current file).

- [ ] **Step 2: Update `handleDiscard` to delete from Supabase**

Replace `handleDiscard`:

```jsx
const handleDiscard = async () => {
  if (preview?.id) {
    setLoading(true)
    const { error } = await supabase.from('recipes').delete().eq('id', preview.id)
    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }
  }
  setPreview(null)
  setUrl('')
  setFiles(null)
  setLoading(false)
}
```

- [ ] **Step 3: Add `handleSkip` function**

Add after `handleDiscard`:

```jsx
const handleSkip = () => {
  onSaved()
}
```

- [ ] **Step 4: Update the preview render block**

Replace the entire preview section (lines 109-168):

```jsx
if (preview) {
  return (
    <div className="recipe-form">
      <h2>Review Recipe</h2>

      <div className="saved-notice">✓ Recipe saved</div>

      {preview.is_vegetarian === false && (
        <div className="warning">This recipe contains meat or fish and is NOT vegetarian.</div>
      )}

      <div className="preview-card">
        <h3>{preview.title}</h3>
        {preview.description && <p className="card-desc">{preview.description}</p>}

        <div className="card-meta">
          {preview.category && <span>{preview.category}</span>}
          {preview.servings && <span>{preview.servings} servings</span>}
          {preview.prep_time_minutes && <span>{preview.prep_time_minutes} min prep</span>}
          {preview.cook_time_minutes && <span>{preview.cook_time_minutes} min cook</span>}
          {preview.bake_time_minutes && <span>{preview.bake_time_minutes} min bake</span>}
        </div>

        {preview.tags?.length > 0 && (
          <div className="card-tags">
            {preview.tags.map(tag => <span key={tag} className="badge tag">{tag}</span>)}
          </div>
        )}

        {preview.ingredients?.length > 0 && (
          <div className="detail-section">
            <h4>Ingredients</h4>
            <ul>
              {preview.ingredients.map((ing, i) => (
                <li key={i}>{ing.quantity} {ing.unit} {ing.name}</li>
              ))}
            </ul>
          </div>
        )}

        {preview.instructions?.length > 0 && (
          <div className="detail-section">
            <h4>Instructions</h4>
            <ol>
              {preview.instructions.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </div>
        )}
      </div>

      <div className="preview-actions">
        <button className="submit-btn" onClick={onSaved}>
          View in List
        </button>
        <button className="discard-btn" onClick={handleDiscard} disabled={loading}>
          {loading ? 'Deleting...' : 'Discard'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Add Skip button to loading state**

Find the loading indicator (line 238):

```jsx
{loading && <p className="status">AI is reading the recipe... this may take a few seconds.</p>}
```

Replace with:

```jsx
{loading && (
  <div>
    <p className="status">AI is reading the recipe... this may take a few seconds.</p>
    <div className="skip-area">
      <button className="skip-btn" onClick={handleSkip}>
        Skip & Save
      </button>
    </div>
  </div>
)}
```

- [ ] **Step 6: Add CSS for new elements**

Add to `frontend/src/index.css` (before the AI Consultation section at line 770):

```css
.skip-area {
  text-align: center;
  margin-top: -20px;
  margin-bottom: 12px;
}

.skip-btn {
  padding: 10px 24px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 0.9rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.skip-btn:hover {
  border-color: var(--green);
  color: var(--green);
}

.saved-notice {
  padding: 10px 12px;
  background: var(--green-bg);
  color: var(--green);
  border-radius: 8px;
  margin-bottom: 14px;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
}
```
