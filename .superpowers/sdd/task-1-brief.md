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
