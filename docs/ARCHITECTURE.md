# Architecture & Infrastructure Map

Snapshot of how the code and the live infrastructure fit together. Verified against the
repo and the live Supabase / Vercel / GitHub Actions state on **2026-10-13** (HEAD `1a1d77c`).
Re-verify anything time-sensitive (counts, URLs, deploy state) before relying on it.

## System overview

```
 Phone / browser (PWA "Nexxt Bite")
        │
        ├── CRUD + Auth ───────────────▶ Supabase (Postgres + Auth + Storage)
        │   supabase-js + anon key           ▲
        │   (RLS enforces ownership)         │ service-role key
        │                                    │ (manual user scoping in code)
        └── AI features ──▶ FastAPI on Cloud Run ──▶ Gemini 2.5 Flash
            fetch + Bearer JWT                  ├──▶ httpx / curl_cffi / cloudscraper (web pages)
                                                ├──▶ img.youtube.com (thumbnails)
                                                └──▶ REWE mobile API (mTLS, via rewerse 1.4.0)

 GitHub (xSpaceCoder/recipy_agent, branch main)
   ├── Vercel Git integration ──▶ frontend build + deploy (every push)
   ├── Actions: deploy-backend.yml ──▶ gcloud run deploy --source ./backend (push to backend/**)
   └── Actions: playwright.yml ──▶ E2E smoke tests (push/PR to main)
```

## Infrastructure (live)

### Supabase
| Item | Value |
|---|---|
| Project ref | `yexthmuusekvpcjsoyem` ("alexandra.goeppert@web.de's Project") |
| Region / PG | eu-north-1, Postgres 17 |
| Tables (public) | `recipes` only (schema matches CLAUDE.md, plus `source_accessed_at timestamptz`, `source_image_urls text[]`) |
| Storage | bucket `source-images`, **public**, no size limit; policies: authenticated INSERT, public SELECT |
| Auth providers in use | `email`, `google` |
| Data (2026-10-13) | 28 recipes, 3 owners, 6 auth users, 9 storage objects |

**RLS on `recipes`** (all `to authenticated`): select own (`user_id = auth.uid()`), select public
(`visibility = 'public'`), insert/update/delete own only.

**Migration history drift:** the remote `supabase_migrations` table records only
`create_recipes_table` and `add_source_metadata`. `003_add_user_auth.sql` *is* applied (columns and
policies exist) but was run by hand, so `supabase db push` would think it's pending. Fix with
`supabase migration repair` before using the CLI for migrations.

**Security advisors (open):**
- `public.update_updated_at` has a mutable `search_path`
- `public.rls_auto_enable()` is `SECURITY DEFINER` and executable by `anon` + `authenticated` via RPC
- Leaked password protection (HaveIBeenPwned) disabled in Auth

### Vercel (frontend)
| Item | Value |
|---|---|
| Project | `recipy-agent` (`prj_kGgRd4tWsZvXID9tRy15JsAHxnSn`), team scope `alexandra-s-projects2` (`team_ZAhRUnd05BK7PgYyYVqowqCK`) |
| Framework / Node | Vite, Node 24.x |
| Production domain | **https://nexxt-bite.vercel.app** (also `recipy-agent-alexandra-s-projects2.vercel.app`, `recipy-agent-git-main-…`) |
| Build | `vercel.json`: `cd frontend && npm install && npm run build` → `frontend/dist`, SPA rewrite `/(.*) → /index.html` |
| Protection | Vercel SSO on all deployments except custom domains (preview URLs need a Vercel login) |
| Env vars | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL` (Cloud Run URL) |
| Latest prod deploy | `1a1d77c` (READY). One past deploy BLOCKED (`d6461ff`). |

Note for MCP use: Vercel calls work when **no `teamId` is passed** (passing the team id returns 403
for this token).

### Google Cloud Run (backend)
| Item | Value |
|---|---|
| GCP project | `recipe-agent-496014` |
| Service | `recipe-agent-api`, region `europe-west1` |
| Deploy | `.github/workflows/deploy-backend.yml` → `google-github-actions/deploy-cloudrun@v2` with `source: ./backend` (Cloud Build builds `backend/Dockerfile`, python:3.11-slim, uvicorn :8080) |
| Trigger | push to `main` touching `backend/**` or the workflow file; or `workflow_dispatch` |
| Auth to GCP | GitHub secret `GCP_SA_KEY` (service-account JSON key) |
| Env vars set by workflow | `ALLOWED_ORIGINS` (from GitHub repo variable, pipe-separated), `REWE_CERT_PATH`, `REWE_KEY_PATH` (strategy: merge) |
| Env vars set manually on the service | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GOOGLE_AI_API_KEY` |
| Secrets | Secret Manager `rewe-cert`, `rewe-key` mounted as files at `/secrets/rewe-cert/latest`, `/secrets/rewe-key/latest` |
| Last deploy | run #15, 2026-09-13, success |

`ALLOWED_ORIGINS` currently = `localhost:5173 | localhost:4173 | nexxt-bite.vercel.app |
recipy-agent-flat6u1k1-…vercel.app` (an old preview URL; other previews will be CORS-blocked).

The cloud container has `gcloud` installed but **no credentials**, so live Cloud Run state
(URL, revisions, logs) can only be read via the GitHub Actions logs or after the user authenticates.

## Code map

### Frontend (`frontend/`, React 19 + Vite 6, no router lib, no state lib)
- `src/lib/supabase.js`: client with `persistSession`, `autoRefreshToken`, `storageKey: 'recipe-agent-auth'`
- `src/lib/useAuth.jsx`: `AuthProvider` / `useAuth()` (session, signOut)
- `src/App.jsx`: gates on auth → `LoginPage`, otherwise list/ingest/form views
- `components/LoginPage.jsx`: email/password sign-in, sign-up, forgot-password, Google OAuth
- `components/RecipeList.jsx`: reads recipes **directly from Supabase**, filters, NL detection → `POST /api/recipes/consult`, delete via Supabase
- `components/RecipeIngest.jsx`: tabs for link / YouTube / photo / REWE → backend `/api/ingest/*`; "Skip & Save" deletes or keeps the auto-saved row
- `components/RecipeForm.jsx`: manual create/edit (direct Supabase)
- `components/RecipeCard.jsx`: horizontal 120×120 card
- `public/sw.js`: network-first cache, skips non-GET and any `*supabase*` host
- `public/manifest.json`: "Nexxt Bite", `share_target` GET → `/ingest?url&text&title`
- `vite.config.js`: `envDir: '../'` (reads root `.env`)

### Backend (`backend/app/`, FastAPI)
- `main.py`: CORS from `ALLOWED_ORIGINS`, routers, `GET /health`
- `config.py`: pydantic-settings (`supabase_url`, `supabase_service_role_key`, `google_ai_api_key`, `rewe_cert_path`, `rewe_key_path`)
- `auth.py`: `get_current_user` validates the Bearer JWT via `supabase.auth.get_user(token)` (one network call per request)
- `database.py`: `get_supabase()` service-role client

| Endpoint | What it does |
|---|---|
| `POST /api/ingest/url` | scrape (`scraper.py`: curl_cffi → cloudscraper → httpx fallback chain, block detection) → Gemini parse → og:image → **auto-save** as `private` |
| `POST /api/ingest/youtube` | Gemini reads the video URL natively → picks hero image from 8 thumbnail candidates → auto-save |
| `POST /api/ingest/image` | multipart images → Gemini multimodal → upload originals to `source-images` → `hero_image_index` → auto-save |
| `POST /api/ingest/rewe/search` | rewerse mTLS search → list with thumbnails |
| `POST /api/ingest/rewe/confirm` | fetch REWE recipe → narrow Gemini `classify_recipe_metadata` (category/season/tags) → auto-save |
| `POST /api/recipes/consult` | loads all visible recipes → Gemini ranks with German seasonal-produce context → `{matches, fallback}` |
| `GET/POST/DELETE /api/recipes/…` | CRUD router; **not used by the frontend** (frontend goes direct to Supabase) |

Services: `ai_parser.py` (all prompts, `gemini-2.5-flash` via the deprecated `google-generativeai`
0.8.0 SDK), `consultation.py`, `scraper.py`, `rewe_api.py`, `youtube.py` (**dead code**: yt-dlp
transcript approach, not imported, yt-dlp not in requirements).

Auto-saved ingested recipes are always `visibility = 'private'`; manual recipes default to `public`.

### Tests
- `backend/tests/`: pytest with mocked Supabase/Gemini (`conftest.py`), `test_ingestion.py`, `test_rewe_api.py`, `test_health.py`
- `tests/*.spec.ts`: Playwright smoke + auth-form tests against Vite dev server with placeholder Supabase env
- `npm run test:backend` uses a Windows venv path (`..\.venv\Scripts\python`); on Linux use `cd backend && python -m pytest tests/ -v`

## Known inconsistencies / risks (as of snapshot)
- `RecipeList.jsx` defaults `API_URL` to `:8000`, `RecipeIngest.jsx` to `:8080` (only matters if `VITE_API_URL` is unset)
- CLAUDE.md "Repository" points to `AI_Daily_Brief`; the actual repo is `xSpaceCoder/recipy_agent`
- `source-images` bucket: any signed-in user can upload anything (no size/type limit), all objects publicly readable
- Backend logging at `DEBUG` in production
- `rewe-test.html` (250 KB) committed at repo root, likely a debugging leftover
- Supabase migration history drift (see above)
