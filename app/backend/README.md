# JobHunter Backend

FastAPI server για το JobHunter SaaS.

## Local setup

```bash
# 1. Install deps (use uv ή pip)
pip install -e .

# 2. Copy env vars
cp .env.example .env
# Edit .env με τα δικά σου API keys

# 3. Start Postgres locally (or use Supabase)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16

# 4. Create database
createdb jobhunter

# 5. Run migrations (TODO: alembic init)
# alembic upgrade head

# 6. Start server
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Structure

```
app/
├── main.py              # FastAPI app entry
├── config.py            # Settings (env vars)
├── schemas.py           # Pydantic models
├── db/
│   ├── models.py        # SQLAlchemy ORM
│   └── session.py       # Async DB sessions
├── api/
│   ├── auth.py          # Clerk JWT dependency
│   ├── users.py         # /api/me
│   ├── cvs.py           # /api/cvs
│   ├── jobs.py          # /api/jobs
│   ├── cover_letters.py # /api/cover-letters
│   ├── applications.py  # /api/applications
│   └── stripe_routes.py # /api/stripe
├── ai/
│   └── cover_letter.py  # Claude integration
├── scrapers/
│   ├── sources.py       # Greenhouse/Lever/Workable fetchers
│   └── matcher.py       # User preference scoring
└── workers/             # Celery tasks (TODO)
```

## Deployment

```bash
# Railway / Render / Fly.io — any Python host
# Procfile or start.sh:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Recommended hosting:
- **Railway** ($5-20/μήνα, easiest Python deploys)
- **Render** ($7/μήνα starter)
- **Fly.io** (free tier sufficient για MVP)

## Phase 1 status

- ✅ Project structure
- ✅ Database schema (8 tables)
- ✅ Auth dependency (Clerk JWT)
- ✅ /api/me + preferences
- ✅ /api/cvs upload + parse
- ✅ /api/jobs/today (DB read)
- ✅ /api/cover-letters/generate (Claude)
- ✅ /api/applications tracking
- ✅ /api/stripe checkout + webhook
- ✅ Job scraper services (Greenhouse/Lever/Workable)
- ✅ User-specific scoring matcher
- ⏳ Alembic migrations
- ⏳ Celery workers (background scraping)
- ⏳ Tests
