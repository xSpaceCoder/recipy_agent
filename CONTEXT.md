# Project Context

## Status: First Slice Working
Frontend (React + Vite PWA), backend (FastAPI), and Supabase database are implemented. Deployment via Vercel (free tier, CI/CD on git push) is configured.

## Who
- **Developer**: Solo — one person, no team
- **Purpose**: Personal education and interest. This is not a commercial product. I want to learn by building, explore agentic coding workflows, and end up with something genuinely useful for my own kitchen.
- **Users**: Me and my boyfriend (two-user app via Supabase Auth)

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
| Hosting | Vercel (free tier, CI/CD via GitHub) | Configured |
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
- Two users (me + boyfriend), simple auth via Supabase Auth — no multi-tenancy needed

## Deployment
- **Frontend hosting**: Vercel (free tier) — auto-deploys on `git push` to `main`, preview URLs for PRs
- **PWA**: Installable on phones, offline caching via service worker, Web Share Target API (share recipes from browser/YouTube directly to the app)
- **Backend hosting**: TBD (Vercel serverless functions, Railway, or Fly.io free tier)
- **CI/CD**: Vercel's built-in GitHub integration — zero-config
