# Project Context

## Status: Greenfield
Nothing is built yet. Only planning documents (markdown files) exist. No code, no database, no deployed infrastructure.

## Who
- **Developer**: Solo — one person, no team
- **Purpose**: Personal education and interest. This is not a commercial product. I want to learn by building, explore agentic coding workflows, and end up with something genuinely useful for my own kitchen.
- **Users**: Just me (single-user app)

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
| Frontend | React (mobile-first) | Not started |
| Backend | Python (FastAPI or Flask) | Not started |
| Database | Supabase (PostgreSQL + Auth + Storage) | Not started |
| AI | Claude API | Not started |
| Repo | GitHub | Not started |
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
- No budget for expensive hosting — prefer free tiers (Supabase free, Vercel/Railway free tier, etc.)
- Single-user, no need for multi-tenancy or complex auth flows
