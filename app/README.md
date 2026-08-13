# 🎯 JobHunter — AI-Powered Job Applications, On Autopilot

Stop wasting your life on job applications. JobHunter scouts 100+ companies daily,
generates personalized cover letters with AI, and pre-fills applications.
**You just show up to the interview.**

## What it does

```
1. Upload your CV (PDF)
2. Set preferences (locations, salary, role types, languages)
3. AI scouts daily across crypto exchanges, fintechs, startups
4. AI writes a unique cover letter for each match
5. One-click apply (Greenhouse/Lever/Workable APIs)
6. Track outcomes in dashboard
```

**Target outcome:** 50 applications/εβδομάδα σε 30 λεπτά (αντί για 30 ώρες).

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 + Tailwind + shadcn/ui |
| Backend | FastAPI (Python 3.12) + SQLAlchemy 2.0 |
| Database | PostgreSQL via Supabase |
| Auth | Clerk |
| AI | Anthropic Claude (haiku για cost, sonnet για premium) |
| Payments | Stripe |
| Hosting | Vercel (frontend) + Railway (backend) |
| Queue | Celery + Redis (Upstash) |

## Project structure

```
JobHunt/app/
├── PRODUCT_VISION.md    Mission, pricing, projections
├── ARCHITECTURE.md      Technical decisions, schema, endpoints
├── README.md            This file
│
├── backend/             FastAPI server
│   ├── pyproject.toml
│   ├── .env.example
│   ├── README.md
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── schemas.py
│       ├── db/          SQLAlchemy models + sessions
│       ├── api/         HTTP routers (auth, users, cvs, jobs, etc.)
│       ├── ai/          Claude integration
│       └── scrapers/    Greenhouse/Lever/Workable fetchers + matcher
│
├── frontend/            Next.js app
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── .env.example
│   ├── README.md
│   └── app/
│       ├── layout.tsx
│       ├── page.tsx           Landing
│       └── dashboard/page.tsx
│
├── docs/                Public docs (TBD)
└── deploy/              Infrastructure config (TBD)
```

## Quick start (local dev)

### Backend
```bash
cd backend
pip install -e .
cp .env.example .env
# Edit .env με τα δικά σου API keys
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local με Clerk keys
npm run dev
```

Backend: http://localhost:8000/docs
Frontend: http://localhost:3000

## Phase 1 status (MVP)

```
✅ Project structure + documentation
✅ Database schema (8 tables)
✅ Auth integration (Clerk JWT verification)
✅ User preferences API
✅ CV upload + PDF parsing
✅ Job scraping (Greenhouse, Lever, Workable)
✅ Multi-tenant matching engine
✅ AI cover letter generation (Claude API με prompt caching)
✅ Stripe checkout + webhook (subscription model)
✅ Application tracking endpoints
✅ Landing page (responsive, Tailwind)
✅ Dashboard skeleton
⏳ Database migrations (Alembic)
⏳ Celery workers για daily scraping cron
⏳ Email notifications
⏳ Mobile UI polish
⏳ Stripe subscription state sync
```

## Phase 2 (post-MVP)

```
□ Browser extension για LinkedIn Easy Apply
□ Interview prep AI assistant (premium tier)
□ Multi-CV per user (one per language)
□ Referral program (free month για 3 referrals)
□ Custom job alerts (Slack/Discord/Telegram)
□ Analytics dashboard (rejection patterns, response times)
□ Premium tier launch
```

## Phase 3 (scale)

```
□ Enterprise tier (career coaches, agencies)
□ White-label option
□ API access
□ Mobile native apps (iOS/Android)
□ Integrations: Notion, Coda, Airtable
□ Anti-ghosting follow-up automation
```

## Revenue model

| Tier | Price | Limits | Target users |
|---|---|---|---|
| Free | €0 | 10 matches/day, no AI letters | Lead capture |
| Pro | €19/μήνα | 50 matches/day, 5 AI letters/day | Active job seekers |
| Premium | €49/μήνα | Unlimited + one-click apply | Aggressive seekers |
| Enterprise | €499/μήνα | 50 sub-accounts | Coaches + agencies |

**Year 1 target:** €100k ARR
**Year 3 target:** €1M ARR → exit window

## Built by

Panos Georgas, με Claude (AI) ως pair programming partner.
Same approach as Aevum Quant. Same productivity multiplier.
