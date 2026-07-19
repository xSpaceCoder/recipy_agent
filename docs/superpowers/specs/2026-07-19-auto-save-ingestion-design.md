# Auto-Save on Recipe Ingestion

**Date:** 2026-07-19
**Status:** Draft

## Problem

Recipe ingestion requires the user to wait for AI processing (5–30s) and manually click "Save Recipe" to persist the result. If the user closes the webapp mid-processing, the result is lost.

## Solution

The backend saves every parsed recipe to Supabase automatically after AI processing completes. The frontend preview becomes a confirmation step instead of a save gate.

No schema changes to the `recipes` table are required. Auto-saved recipes default to `visibility: 'private'`.

## Architecture

### Backend: `backend/app/routers/ingestion.py`

A new helper function `_save_recipe_to_supabase` inserts the parsed recipe into Supabase using the service role key. It explicitly maps known columns and strips AI-only fields (`is_vegetarian`, `error`, `hero_image_index`, `source_image_urls`, `source_accessed_at`).

Each of the three ingestion endpoints (`/api/ingest/url`, `/api/ingest/youtube`, `/api/ingest/image`) calls this helper after successful AI parsing, before returning the response. The returned recipe dict includes `"id"` (UUID from DB) and `"saved": true`.

Auto-saved recipes default to `visibility: 'private'` (overridable if AI returns a visibility field).

### Frontend: `frontend/src/components/RecipeIngest.jsx`

- **Loading state**: Shows a "Skip & Save" button alongside the spinner. Clicking it calls `onSaved()` to navigate to the recipe list immediately. The backend request continues independently and saves the recipe.
- **Preview state**: Recipe is already saved. Shows "✓ Recipe saved!" indicator, then auto-navigates to the recipe list after 2 seconds (countdown shown). User can also click "View in List" immediately or "Discard" to delete.
- **Discard**: Now deletes the recipe from Supabase (via Supabase JS client) instead of just clearing local state.
- **`handleSave` function**: Removed entirely.

### Data Flow

```
User submits → Backend parses AI → Backend saves to Supabase → Returns {id, saved, ...data}
                                                                      │
                                          ┌───────────────────────────┤
                                          ▼                           ▼
                                   Preview shown               Skip clicked during
                                   (already saved)             loading → navigate away
                                   [View in List] [Discard]    (recipe saved on backend)
```

## Error Handling

| Condition | Behavior |
|---|---|
| AI parsing fails | HTTP 422 raised before save. No recipe created. |
| Supabase save fails | HTTP 500 raised. No recipe created. Error shown to user. |
| Client disconnects mid-processing | Save completes (runs before response attempt). Response send fails silently. |
| Cloud Run 60s timeout | Request terminated. Same as today — no save. |
| User discards after save | Recipe deleted from Supabase via JS client. |

## Testing

### Backend
- Mock Gemini + Supabase in conftest.py
- Verify `_save_recipe_to_supabase` is called for each endpoint
- Verify `is_vegetarian`, `error`, `hero_image_index`, `source_image_urls`, `source_accessed_at` are stripped before insert
- Verify `user_id` is set from auth
- Verify AI parse failure → no save attempt
- Verify Supabase save failure → HTTP 500

### Frontend E2E
- Submit a URL → verify recipe appears in recipe list without clicking Save
- Click Skip during loading → verify navigation to list
- Click Discard on preview → verify recipe removed from Supabase
