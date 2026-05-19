# Project Context

## Status: AI Consultation Implemented
Frontend (React + Vite PWA), backend (FastAPI), and Supabase database are implemented. Deployment via Vercel (free tier, CI/CD on git push) is configured. Multi-user authentication (Google OAuth + Email magic link) with per-user recipe ownership and public/private visibility is implemented. AI-powered recipe consultation (natural language search via Gemini, bilingual DE/EN, season-aware) is implemented.

## Who
- **Developer**: Solo — one person, no team
- **Purpose**: Personal education and interest. This is not a commercial product. I want to learn by building, explore agentic coding workflows, and end up with something genuinely useful for my own kitchen.
- **Users**: Me + friends/family (multi-user via Supabase Auth with Google OAuth + Email magic link)

## Domain: Recipe Management
I cook regularly — casual dinners at home and cakes/desserts I bring to friends. My recipes are currently scattered across:
- Printed recipes (physical paper)
- Bookmarked web links
- Instagram Reels and YouTube Shorts (video format with visual instructions)

I'm vegetarian (no meat, no fish; I do eat gummi bears, figs, parmesan). Recipes should be evaluated and tagged accordingly.

## What I'm Building
A **Recipe Agent** — a mobile-first web app backed by AI that:
1. **Ingests** recipes from any format (photo, video link, web URL, manual entry) and stores them in a standardized, searchable database
2. **Consults** me on what to cook based on natural language queries, available ingredients, time constraints, and dietary preferences

## Tech Stack (Planned)
| Layer | Technology | Status |
|-------|-----------|--------|
| Frontend | React (mobile-first) | Started |
| Backend | Python (FastAPI or Flask) | Started |
| Database | Supabase (PostgreSQL + Auth + Storage) url stored in env | Started |
| AI | Google AI Studio API (key stored in env) | Started |
| Frontend Hosting | Vercel (free tier, CI/CD via GitHub) | Configured |
| Backend Hosting | Google Cloud Run (free tier, europe-west1) | Deployed |
| Private Repo | GitHub: https://github.com/xSpaceCoder/AI_Daily_Brief | Active |
| Dev tool | Claude Code (Opus 4.6) in VS Code | Active |


## Learning Goals
- Build a full-stack app end-to-end with agentic coding assistance
- Understand how to integrate LLMs into a real product workflow (parsing, tagging, recommendation)
- Explore Supabase as a backend-as-a-service
- Get comfortable with React for mobile-first web UIs
- Experiment with multimodal input (images, video metadata) feeding into structured data

## Constraints
- Solo developer, limited time — favor simplicity and "good enough" over perfection
- Behind corporate proxy — package installs may require VPN disconnect
- No budget for expensive hosting — prefer free tiers (Supabase free, Vercel free tier)
- Multiple users (me + friends/family) via Supabase Auth (Google OAuth + Email magic link), per-user recipe ownership with public/private visibility

## Deployment
- **Frontend hosting**: Vercel (free tier) — auto-deploys on `git push` to `main`, preview URLs for PRs
- **Backend hosting**: Google Cloud Run (free tier, europe-west1) — containerized FastAPI, auto-deploys via GitHub Actions on push to `backend/**`, manual trigger via `workflow_dispatch`
- **PWA**: Installable on phones, offline caching via service worker (excludes Supabase auth from cache), Web Share Target API (share recipes from browser/YouTube directly to the app)
- **Session persistence**: Supabase client uses `localStorage` with `autoRefreshToken` — users stay logged in as long as they open the app once per 7 days (free tier refresh token window)
- **CI/CD**: Vercel GitHub integration for frontend; GitHub Actions + `google-github-actions/deploy-cloudrun@v2` for backend
- **Backend env vars**: Set on Cloud Run directly (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GOOGLE_AI_API_KEY`, `ALLOWED_ORIGINS` using `|` as separator)
- **CORS**: Managed via `ALLOWED_ORIGINS` env var on Cloud Run (pipe-separated origins)
- **AI Consultation**: Natural language search via `POST /api/recipes/consult` — auto-detected in frontend (4+ words or NL indicators), Gemini ranks all user-accessible recipes with seasonal context, bilingual DE/EN, graceful fallback to Supabase full-text search
