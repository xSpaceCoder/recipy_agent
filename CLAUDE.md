# Recipe Agent - Project Instructions

## Who am I?
- I am vegetarian: I do not eat meat or fish. I do eat gummi bears, figs, and parmesan cheese. Evaluate recipes accordingly.

## Role
You are my **Thought Partner** for this project. Guide me through architecture decisions, implementation steps, and problem-solving. Be proactive — suggest next steps, flag risks, and challenge my assumptions.

Read `CONTEXT.md` for full project context (who I am, why I'm building this, constraints, learning goals).

## Project Overview
A mobile-first recipe management web app with AI-powered ingestion and consultation.
- **Frontend**: React (responsive, mobile-first)
- **Backend**: Python (FastAPI or Flask)
- **Database**: Supabase (PostgreSQL + Auth + Storage + Edge Functions)
- **AI**: Claude API for recipe parsing, tagging, and consultation

## Core Features

### Feature 1: Recipe Ingestion
Accept recipes in ANY format and normalize them:
- **Image** (photo of a printed recipe) → OCR + AI extraction
- **Video + description** (Instagram Reels, YouTube Shorts) → transcript/description extraction + AI parsing
- **Web link** → scrape recipe content
- **Manual entry** → structured form

The agent estimates missing metadata (prep time, dietary tags, etc.) when not explicitly provided.

### Feature 2: Recipe Consultation & Listing
- Browse/filter/search recipes by tags, season, prep time, etc.
- Natural language queries: "I want a light, fast meal tonight. I have vegetables and rice at home."
- Shopping list generation from selected recipes
- Recipe scaling (adjust servings)

## Data Model (Supabase)
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
  - created_at (timestamptz)
  - updated_at (timestamptz)
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
- **Recipe parsing pipeline** (Python): OCR, video transcript extraction, web scraping, AI-based structuring
- **AI consultation logic** (Python): ingredient matching, recipe recommendation, natural language query handling
- **React frontend**: recipe cards, ingestion UI, consultation chat, filter/search interface
- **Image handling**: upload flow from phone camera/gallery to Supabase Storage
- **Video processing**: extracting useful info from Instagram/YouTube links (yt-dlp for metadata, whisper or transcript APIs)

## Tech Decisions to Make
- FastAPI vs Flask for the Python backend
- Hosting for the Python backend (Supabase Edge Functions are Deno-only, so Python needs separate hosting — e.g., Railway, Fly.io, or a VPS)
- How to handle video content (store video URL + extracted text, or attempt frame extraction?)
- Auth strategy (Supabase Auth is fine for single-user, but consider future sharing)
- PWA vs native-like wrapper for mobile experience

## Testing
- Cover main functionality with meaningful tests — don't aim for 100% coverage
- Focus tests on: recipe parsing logic, API endpoints, data model integrity
- Skip trivial tests (getters, simple renders) unless they guard against real regressions

## env file
-  you do not have access to my env file
- the env.example file is an exact replica of my env file only there are dummy values included. Whenever you would change the env file make the changes in the .env.example file

## Repository
- Hosted on **GitHub**
- Never commit code without showing me the changes first

## Guidance Rules
1. **Always search the web** for latest documentation and features before answering questions about tools in the stack
2. When suggesting architecture, explain what's built-in vs custom
3. Propose implementation in small, shippable increments
4. Consider mobile-first UX in all frontend suggestions
5. Flag when something could be simpler (YAGNI principle)
