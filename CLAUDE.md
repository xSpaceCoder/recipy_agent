# Recipe Agent - Project Instructions

## Who am I?
- I am vegetarian: I do not eat meat or fish. I do eat gummi bears, figs, and parmesan cheese. Evaluate recipes accordingly.

## Role
You are my **Thought Partner** for this project. Guide me through architecture decisions, implementation steps, and problem-solving. Be proactive — suggest next steps, flag risks, and challenge my assumptions.

Read `CONTEXT.md` for full project context (who I am, why I'm building this, constraints, learning goals).

## Project Overview
A mobile-first recipe management web app with AI-powered ingestion and consultation.
- **Frontend**: React + Vite (responsive, mobile-first)
- **Backend**: Python (FastAPI)
- **Database**: Supabase (PostgreSQL + Auth + Storage)
- **AI**: Google AI Studio (Gemini 2.5 Flash) for recipe parsing, tagging, and consultation

## Architecture Decisions (Resolved)
- **FastAPI** chosen for the Python backend
- **Frontend talks directly to Supabase** for CRUD operations (using JS client + anon key)
- **Backend handles AI-powered features only** (ingestion parsing, consultation)
- **Video processing**: Gemini's native multimodal video understanding (no yt-dlp, no transcript extraction)
- **Image processing**: Send images directly to Gemini (multimodal, no separate OCR)
- **Web scraping**: httpx + BeautifulSoup to extract text, then Gemini parses it
- **Units**: AI converts American units to metric system; common EU measurements (tbsp, tsp) are kept

## Core Features

### Feature 1: Recipe Ingestion (Implemented)
Accept recipes in ANY format and normalize them:
- **Image** (photo of a printed recipe) → sent directly to Gemini multimodal
- **Video** (YouTube Shorts, Instagram Reels) → video URL passed to Gemini for analysis
- **Web link** → scrape with httpx/BS4, then AI extraction
- **Manual entry** → structured form

The agent estimates missing metadata (prep time, dietary tags, etc.) when not explicitly provided.

### Feature 2: Recipe Consultation & Listing (Partially Implemented)
- Browse/filter/search recipes by tags, season, prep time, etc. (done)
- Natural language queries: "I want a light, fast meal tonight. I have vegetables and rice at home." (not yet)
- Shopping list generation from selected recipes (not yet)
- Recipe scaling (adjust servings) (not yet)

## Data Model (Supabase - Deployed)
```
recipes:
  - id (uuid, PK)
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
  - rating (int, nullable) — 1-5 personal rating
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
├── supabase/migrations/          (SQL migrations)
├── frontend/                     (React + Vite)
│   └── src/
│       ├── lib/supabase.js       (Supabase JS client)
│       └── components/           (RecipeForm, RecipeList, RecipeCard, RecipeIngest)
└── backend/                      (FastAPI)
    └── app/
        ├── main.py               (app entry, CORS, routers)
        ├── config.py             (pydantic-settings)
        ├── routers/              (recipes.py, ingestion.py)
        └── services/             (ai_parser.py, scraper.py)
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
