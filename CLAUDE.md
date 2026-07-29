# Recipe Agent - Project Instructions

## Who am I?
- I am vegetarian: I do not eat meat or fish. I do eat gummi bears, figs, and parmesan cheese. Evaluate recipes accordingly.

## Role
You are my **Thought Partner** for this project. Guide me through architecture decisions, implementation steps, and problem-solving. Be proactive — suggest next steps, flag risks, and challenge my assumptions.

Read `CONTEXT.md` for full project context (who I am, why I'm building this, constraints, learning goals).

## Project Overview
A mobile-first recipe management PWA with AI-powered ingestion and consultation.
- **Frontend**: React + Vite (PWA, responsive, mobile-first)
- **Backend**: Python (FastAPI)
- **Database**: Supabase (PostgreSQL + Auth + Storage)
- **AI**: Google AI Studio (Gemini 2.5 Flash) for recipe parsing, tagging, and consultation
- **Frontend Hosting**: Vercel (free tier, auto-deploy on push via GitHub CI/CD)
- **Backend Hosting**: Google Cloud Run (free tier, europe-west1, containerized FastAPI)
- **Users**: me and friends/family

## Architecture Decisions (Resolved)
- **FastAPI** chosen for the Python backend
- **Frontend talks directly to Supabase** for CRUD operations (using JS client + anon key)
- **Backend handles AI-powered features only** (ingestion parsing, consultation)
- **Video processing**: Gemini's native multimodal video understanding (no yt-dlp, no transcript extraction)
- **Image processing**: Send images directly to Gemini (multimodal, no separate OCR)
- **Web scraping**: httpx + BeautifulSoup to extract text, then Gemini parses it
- **REWE integration**: REWE.de uses Cloudflare Bot Management (hard 403 from Cloud Run datacenter IPs). Instead of scraping, the app uses REWE's mobile mTLS-protected API via the `rewerse` Python package. A dedicated "REWE" tab in the ingestion UI lets users search by recipe title, pick from results, and import directly. Certificate files extracted from the REWE Android APK are configured via `REWE_CERT_PATH`/`REWE_KEY_PATH` env vars.
- **Units**: AI converts American units to metric system; common EU measurements (tbsp, tsp) are kept
- **Frontend hosting**: Vercel free tier — auto-deploys frontend on `git push` to `main`; PRs get preview URLs
- **Backend hosting**: Google Cloud Run (free tier, europe-west1) — auto-deploys via GitHub Actions on push to `backend/**`
- **PWA**: Installable on phones, service worker for offline caching, Web Share Target API for sharing recipes directly from browser/YouTube (like sharing to WhatsApp)
- **Auth**: Supabase Auth with Google OAuth + Email magic link; full-screen login page gates the app
- **Session persistence**: Supabase client configured with `persistSession: true`, `autoRefreshToken: true`, dedicated `storageKey`. Users stay logged in as long as they open the app once within 7 days (free tier refresh token window). Service worker excludes Supabase requests from caching to avoid stale auth responses.
- **Multi-user model**: Each recipe has a `user_id` (owner) and `visibility` (public/private). Users see own recipes + public recipes from others. Rating and edit/delete are owner-only.
- **Backend auth**: All API endpoints verify Supabase JWT via `Authorization: Bearer` header; service role key used for DB access with manual user-scoping

## Core Features

### Feature 1: Recipe Ingestion (Implemented)
Accept recipes in ANY format and normalize them:
- **Image** (photo of a printed recipe) → sent directly to Gemini multimodal
- **Video** (YouTube Shorts, Instagram Reels) → video URL passed to Gemini for analysis
- **Web link** → scrape with httpx/BS4, then AI extraction
- **REWE** → dedicated tab in ingestion UI; user searches by recipe title via REWE's mobile mTLS API, picks from results, recipe is imported directly with `source_url` set to REWE's `detailUrl`
- **Manual entry** → structured form

The agent estimates missing metadata (prep time, dietary tags, etc.) when not explicitly provided.
- **Auto-save on ingestion**: After AI parsing, recipes are saved directly to Supabase. Preview step shows a streamlined "Skip & Save" flow.
- **AI hero image selection**: For photo uploads, Gemini identifies which uploaded image best shows the finished dish via `hero_image_index`. For YouTube, Gemini evaluates up to 8 thumbnail candidates (4 quality levels + 4 storyboard frames) and selects the one with the best dish shot.

### Feature 2: Recipe Consultation & Listing (Implemented)
- Browse/filter/search recipes by tags, season, prep time, etc. (done)
- Natural language queries via Gemini: auto-detected in search bar (4+ words or NL indicators), bilingual DE/EN, season-aware with German produce seasonality, returns ranked recipes with 1-sentence explanations for top 5 matches, graceful fallback to text search on failure (done)
- **Horizontal card layout**: 120×120px 1:1 image on the left, content with tags on the right. Title truncates at 2 lines, category badge sits right of the title. (done)
- Shopping list generation from selected recipes (not yet)
- Recipe scaling (adjust servings) (not yet)

## Data Model (Supabase - Deployed)
```
recipes:
  - id (uuid, PK)
  - user_id (uuid, FK → auth.users, NOT NULL) — recipe owner
  - title (text)
  - description (text)
  - ingredients (jsonb) — [{name, quantity, unit}]
  - instructions (text[]) — ordered steps
  - servings (int)
  - prep_time_minutes (int)
  - cook_time_minutes (int, nullable)
  - bake_time_minutes (int, nullable)
  - chill_time_minutes (int, nullable)
  - freeze_time_minutes (int, nullable)
  - tags (text[]) — ["vegetarian", "vegan", "gluten-free", "light", "cozy", "fiber-rich", ...]
  - category (text) — "dinner", "cake", "dessert", "soup/stew"
  - season (text[]) — ["spring", "summer", "autumn", "winter", "all"]
  - rating (int, nullable) — 1-5 personal rating (only visible to owner)
  - visibility (text, NOT NULL, default 'public') — 'public' or 'private'
  - image_url (text, nullable) — stored in Supabase Storage
  - source_url (text, nullable) — original link
  - source_type (text) — "image", "video", "link", "manual"
  - fts (tsvector) — generated full-text search column
  - created_at (timestamptz)
  - updated_at (timestamptz)
```

## Project Structure
```
├── .env                          (secrets — gitignored)
├── .env.example                  (template with dummy values)
├── .mcp.json                     (MCP server config — gitignored)
├── vercel.json                   (Vercel deployment config — build + SPA routing)
├── .github/workflows/
│   ├── deploy-backend.yml        (GitHub Actions — auto-deploy backend to Cloud Run)
│   └── playwright.yml            (GitHub Actions — E2E tests on push/PR)
├── tests/                          (Playwright E2E tests)
│   └── smoke.spec.ts             (app load + login page smoke tests)
├── supabase/migrations/          (SQL migrations)
├── frontend/                     (React + Vite PWA)
│   ├── index.html                (links manifest, registers service worker)
│   ├── public/
│   │   ├── manifest.json         (PWA manifest + share_target config)
│   │   ├── sw.js                 (service worker — offline caching)
│   │   └── icons/                (PWA icons: 192px, 512px)
│   └── src/
│       ├── lib/supabase.js       (Supabase JS client)
│       ├── lib/useAuth.jsx       (Auth context + hook — session, sign out)
│       └── components/           (LoginPage, RecipeForm, RecipeList, RecipeCard, RecipeIngest)
└── backend/                      (FastAPI, containerized for Cloud Run)
    ├── Dockerfile                (Python 3.11-slim, uvicorn on port 8080)
    ├── .dockerignore             (excludes .env, __pycache__, venv)
    ├── pytest.ini                (pytest config — testpaths, pythonpath)
    ├── tests/                    (backend unit/integration tests)
    │   ├── conftest.py           (test client fixture, mocked deps)
    │   └── test_health.py        (health endpoint smoke test)
    └── app/
        ├── main.py               (app entry, CORS via ALLOWED_ORIGINS env var, routers)
        ├── config.py             (pydantic-settings)
        ├── auth.py               (JWT verification dependency via Supabase get_user)
        ├── routers/              (recipes.py, ingestion.py, consultation.py)
        └── services/             (ai_parser.py, scraper.py, consultation.py, rewe_api.py)
```

## What Supabase Provides Out of the Box
- PostgreSQL database with Row Level Security
- Auth (email/password, OAuth, magic link)
- Realtime subscriptions
- Storage (for recipe images)
- Edge Functions (Deno-based serverless functions)
- Auto-generated REST API (PostgREST) and GraphQL
- Full-text search via PostgreSQL `tsvector`
- Supabase JS client for frontend

## What Needs Custom Building
- **Recipe parsing pipeline** (Python): web scraping, AI-based structuring via Gemini
- **AI consultation logic** (Python): ingredient matching, recipe recommendation, natural language query handling
- **React frontend**: recipe cards, ingestion UI, consultation chat, filter/search interface
- **Image handling**: upload flow from phone camera/gallery to Supabase Storage

## Testing
- Cover main functionality with meaningful tests — don't aim for 100% coverage
- Focus tests on: recipe parsing logic, API endpoints, data model integrity
- Skip trivial tests (getters, simple renders) unless they guard against real regressions

### Running Tests
- **Backend**: `cd backend && ..\.venv\Scripts\python -m pytest tests/ -v`
- **Frontend E2E**: `npx playwright test` (auto-starts Vite dev server)
- **All**: `npm test` (runs backend then E2E)
- Backend tests mock Supabase/Gemini via conftest.py — no real credentials needed

### Backend Virtual Environment
- The project uses a Python venv at `.venv/` (project root, not inside backend/)
- **Always use the venv** when running backend commands: `..\.venv\Scripts\python` (Windows)
- To activate: `.venv\Scripts\activate` (PowerShell)
- All dependencies from `requirements.txt` are installed in this venv

## env file
- you do not have access to my env file
- the env.example file is an exact replica of my env file only there are dummy values included. Whenever you would change the env file make the changes in the .env.example file

## Repository
- Hosted on **GitHub** (private): https://github.com/xSpaceCoder/AI_Daily_Brief
- Never commit code without showing me the changes first

## Guidance Rules
1. **Always search the web** for latest documentation and features before answering questions about tools in the stack
2. When suggesting architecture, explain what's built-in vs custom
3. Propose implementation in small, shippable increments
4. Consider mobile-first UX in all frontend suggestions
5. Flag when something could be simpler (YAGNI principle)
