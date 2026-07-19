# Task 1 Report: Backend — Add save helper + update ingestion endpoints

## What was implemented

1. **`_SAVE_FIELDS` constant** — whitelist of recipe fields that are safe to persist to Supabase (strips `is_vegetarian`, `error`, `hero_image_index`, `source_image_urls`, `source_accessed_at`)
2. **`_save_recipe_to_supabase(sb, recipe, user_id) -> dict`** helper — inserts filtered recipe data into the `recipes` table with `visibility` defaulting to `"private"`
3. **Save block added to all 3 ingestion endpoints** (`/api/ingest/url`, `/api/ingest/youtube`, `/api/ingest/image`) — each calls `_save_recipe_to_supabase` before returning, then enriches the response with `id` and `saved: true`

## Files changed

- `backend/app/routers/ingestion.py` — 47 lines added

## Test results

Ran `backend/.venv/Scripts/python -m pytest tests/ -v`:
- `test_health_endpoint` — **ERROR** (pre-existing: `conftest.py` patches `app.database.get_supabase` which doesn't exist; not related to this task)

The test failure is a pre-existing infrastructure issue in `conftest.py`, not caused by the changes.

## Self-review findings

- All changes match the brief exactly — code blocks were used verbatim
- `_SAVE_FIELDS` correctly excludes fields like `error`, `is_vegetarian`, `hero_image_index`, `source_image_urls`, `source_accessed_at`
- `data.setdefault("visibility", "private")` ensures private default
- Save happens BEFORE response is sent (per requirements)
- No schema changes to `recipes` table were required

## Concerns

- Test infrastructure needs fixing (`conftest.py` references a non-existent `app.database` module) — should be patching `app.routers.ingestion._get_supabase` instead
- The `.venv` didn't exist and had to be created; the pinned versions in `requirements.txt` (e.g., `pydantic-core==2.33.0`) don't have prebuilt wheels for Python 3.14, requiring `--only-binary :all:` fallback or version bump
