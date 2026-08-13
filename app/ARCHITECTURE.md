# 🏗️ JobHunter — Technical Architecture

## High-Level Stack

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   FRONTEND (Vercel)                                     │
│   ┌─────────────────────────────────────────┐           │
│   │  Next.js 14 + App Router + Tailwind     │           │
│   │  shadcn/ui components                    │           │
│   │  Clerk Auth (login/signup)               │           │
│   └─────────────────────────────────────────┘           │
│                                                         │
│                       │ HTTPS REST                      │
│                       ▼                                 │
│                                                         │
│   BACKEND (Railway / Render)                            │
│   ┌─────────────────────────────────────────┐           │
│   │  FastAPI (Python 3.12)                  │           │
│   │  ┌─────────┬─────────┬────────────────┐ │           │
│   │  │  Users  │  Jobs   │  Applications  │ │           │
│   │  ├─────────┼─────────┼────────────────┤ │           │
│   │  │  CVs    │ Cover   │  Scrapers      │ │           │
│   │  │         │ Letters │                │ │           │
│   │  └─────────┴─────────┴────────────────┘ │           │
│   └─────────────────────────────────────────┘           │
│                                                         │
│       │              │              │                   │
│       ▼              ▼              ▼                   │
│                                                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│   │ Postgres │  │  Claude  │  │  Stripe  │             │
│   │ Supabase │  │   API    │  │ Payments │             │
│   └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
│   ┌──────────┐  ┌──────────────────────────┐            │
│   │ S3 Files │  │  Cron Workers            │            │
│   │ Supabase │  │  - Daily job scraper     │            │
│   │ Storage  │  │  - Email notifications   │            │
│   └──────────┘  └──────────────────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Technology Choices με Reasoning

### Frontend

```
FRAMEWORK: Next.js 14 (App Router)
WHY:
  ✓ Industry standard, easy to hire devs
  ✓ Server components για SEO landing page
  ✓ API routes για lightweight endpoints
  ✓ Vercel deploy = zero config

STYLING: Tailwind CSS + shadcn/ui
WHY:
  ✓ Component library = ταχύτητα
  ✓ Customizable, owned components
  ✓ Modern aesthetic out of box

AUTH: Clerk (or Supabase Auth as backup)
WHY:
  ✓ Magic links, social login built-in
  ✓ JWT tokens for backend auth
  ✓ €0 για first 10k MAU
  ✓ No password reset hell
```

### Backend

```
FRAMEWORK: FastAPI (Python 3.12)
WHY:
  ✓ Best Python web framework 2026
  ✓ Async by default = high concurrency
  ✓ Auto OpenAPI docs
  ✓ Pydantic v2 = type safety
  ✓ Existing _job_hunter.py code reusable

DATABASE: PostgreSQL via Supabase
WHY:
  ✓ Free tier: 500MB storage, 2GB transfer/μήνα
  ✓ Realtime subscriptions built-in
  ✓ Storage bucket για CVs (€0.021/GB)
  ✓ Auth integration
  ✓ Scales to $25/μήνα for Pro tier

ORM: SQLAlchemy 2.0 (async)
WHY:
  ✓ Mature, well-documented
  ✓ Migration support via Alembic
  ✓ Async support για FastAPI

JOB QUEUE: Celery + Redis (Upstash)
WHY:
  ✓ Daily scraping = background work
  ✓ Email sending async
  ✓ Upstash Redis free tier sufficient για MVP
```

### AI Layer

```
PROVIDER: Anthropic Claude API
WHY:
  ✓ Best at instruction following (cover letters)
  ✓ Prompt caching = 60% cost reduction
  ✓ Long context (200k tokens) = full CV + job desc
  ✓ Better Greek language quality than GPT-4

MODEL: claude-haiku-4-5 για cover letters (cheap, fast)
       claude-sonnet-4-7 για premium features

COST ESTIMATE:
  Cover letter: ~3k input + 1k output tokens
  = $0.003 input + $0.005 output = $0.008 per letter
  = €0.0074
  
  Pro tier 5 letters/day × 30 = 150 letters/μήνα
  Cost: €1.11/μήνα per Pro user
  Margin: €19 - €1.11 = €17.89 (94%)
```

### Payments

```
PROVIDER: Stripe
WHY:
  ✓ European entity (Stripe Ireland)
  ✓ SEPA + cards + Apple/Google Pay
  ✓ Subscription management built-in
  ✓ Tax compliance automated (Stripe Tax)
  ✓ €0 setup, 1.5% + €0.25 per EU transaction
```

### Hosting / DevOps

```
FRONTEND: Vercel
  Free tier: 100GB bandwidth/μήνα → ~10k users
  Pro tier: $20/μήνα when needed

BACKEND: Railway (preferred) or Render
  Railway: $5 starter, $20/μήνα for production
  Render: $7/μήνα starter, similar pricing

DATABASE: Supabase
  Free: 500MB → ~5k users
  Pro: $25/μήνα → ~50k users

OBSERVABILITY:
  Sentry για errors (free tier 5k events/μήνα)
  PostHog για analytics (free tier 1M events/μήνα)
  Better Stack για uptime (free tier 3 monitors)
  
TOTAL HOSTING COST:
  Month 0-3:   $0 (all free tiers)
  Month 3-12:  $50-100/μήνα
  Month 12+:   $200-500/μήνα at 5k+ users
```

## Database Schema (Phase 1 — MVP)

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id TEXT UNIQUE NOT NULL,  -- from auth provider
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  tier TEXT NOT NULL DEFAULT 'free',  -- 'free' | 'pro' | 'premium'
  stripe_customer_id TEXT,
  preferences JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- CVs uploaded by users
CREATE TABLE cvs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,         -- "My EN CV", "Spanish CV"
  language TEXT NOT NULL,      -- 'en', 'el', 'es', 'de'...
  storage_url TEXT NOT NULL,   -- Supabase Storage path
  parsed_text TEXT,            -- Extracted text για AI
  is_primary BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User preferences για job matching
-- Stored as JSONB in users.preferences:
-- {
--   "locations": ["Madrid", "Remote EU", "Athens"],
--   "salary_min": 35000,
--   "salary_max": 60000,
--   "languages": ["en", "el"],
--   "roles": ["Customer Success", "Account Manager"],
--   "industries": ["fintech", "crypto", "saas"],
--   "exclude_keywords": ["software engineer", "developer"],
--   "experience_level": "entry",  -- entry/mid/senior
--   "remote_only": false,
--   "willing_to_relocate": true
-- }

-- Jobs discovered by scrapers
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL,        -- 'greenhouse', 'lever', 'linkedin'
  external_id TEXT NOT NULL,   -- ID στο source
  company TEXT NOT NULL,
  title TEXT NOT NULL,
  location TEXT,
  description TEXT,
  url TEXT NOT NULL,
  salary_min INTEGER,
  salary_max INTEGER,
  remote BOOLEAN,
  posted_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  raw_data JSONB,              -- full original
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(source, external_id)
);

CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_posted_at ON jobs(posted_at DESC);

-- User → Job matches (computed daily)
CREATE TABLE job_matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  relevance_score INTEGER NOT NULL,   -- 0-100
  match_reasons JSONB,                -- why matched
  status TEXT DEFAULT 'pending',      -- pending/saved/applied/ignored/rejected
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, job_id)
);

CREATE INDEX idx_matches_user_score ON job_matches(user_id, relevance_score DESC);

-- Cover letters generated per match
CREATE TABLE cover_letters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id UUID REFERENCES job_matches(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  language TEXT NOT NULL,
  content TEXT NOT NULL,
  ai_model TEXT,           -- 'claude-haiku-4-5'
  tokens_used INTEGER,
  generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Applications (tracking what user actually applied to)
CREATE TABLE applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  match_id UUID REFERENCES job_matches(id),
  cover_letter_id UUID REFERENCES cover_letters(id),
  applied_at TIMESTAMPTZ DEFAULT NOW(),
  method TEXT,             -- 'one_click' | 'manual' | 'auto'
  status TEXT DEFAULT 'sent',
  response_received_at TIMESTAMPTZ,
  response_status TEXT,    -- 'interview' | 'rejected' | 'ghosted'
  notes TEXT
);

-- Subscription state (from Stripe)
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  stripe_subscription_id TEXT UNIQUE,
  tier TEXT NOT NULL,
  status TEXT,             -- active/canceled/past_due
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  canceled_at TIMESTAMPTZ
);
```

## API Endpoints (Phase 1)

```
AUTH (handled by Clerk):
  POST  /auth/signup
  POST  /auth/login
  POST  /auth/logout

USERS:
  GET   /api/me                 → current user + tier + preferences
  PATCH /api/me/preferences     → update job preferences

CVs:
  POST  /api/cvs                → upload CV (multipart)
  GET   /api/cvs                → list user CVs
  DELETE /api/cvs/{id}          → remove CV
  POST  /api/cvs/{id}/primary   → mark as primary

JOBS:
  GET   /api/jobs/today         → today's matches (limited by tier)
  GET   /api/jobs/{id}          → single job detail
  POST  /api/jobs/{id}/save     → save for later
  POST  /api/jobs/{id}/ignore   → don't show again

COVER LETTERS:
  POST  /api/cover-letters/generate     → AI-generate for job match
  GET   /api/cover-letters/{id}         → fetch generated text
  PATCH /api/cover-letters/{id}         → edit before applying

APPLICATIONS:
  POST  /api/applications               → mark as applied
  GET   /api/applications               → list of applications με status
  PATCH /api/applications/{id}/status   → update outcome

PAYMENTS (Stripe webhooks):
  POST  /api/stripe/checkout           → create checkout session
  POST  /api/stripe/webhook            → handle subscription events
  GET   /api/billing/portal            → customer portal URL

ADMIN (internal):
  GET   /admin/stats                   → MRR, users, conversions
  POST  /admin/scrape                  → trigger manual scrape
```

## Background Jobs (Celery)

```
DAILY:
  • run_all_scrapers          (3am UTC) — fetch new jobs
  • compute_user_matches       (6am UTC) — score jobs per user
  • send_daily_emails          (7am user TZ) — match notifications
  • cleanup_expired_jobs       (4am UTC) — remove old listings

WEEKLY:
  • analytics_rollup           (Sunday) — user engagement stats
  • churn_reactivation         (Wednesday) — re-engage dormant users

ON-DEMAND:
  • generate_cover_letter      (user click) — Claude API call
  • parse_cv                   (CV upload) — extract text + metadata
  • notify_response            (status change) — email user
```

## Security Considerations

```
• All API endpoints require auth (Clerk JWT)
• CV files server-side parsed, never client-exposed
• PII (email, salary) encrypted at rest (Supabase default)
• Rate limiting: 100 req/min per user (FastAPI middleware)
• CORS: only frontend domain whitelisted
• Webhook signature verification (Stripe + Clerk)
• Database backups: Supabase daily auto-snapshots
• GDPR: data export + delete endpoints required (Article 17, 20)
```

## Cost Per User Estimate (Pro tier)

```
COSTS:
  Hosting (amortized):     €0.10
  Supabase storage:        €0.05
  Stripe fees (1.5%+€0.25):€0.54
  Claude API (150 letters):€1.11
  Email (SendGrid):        €0.02
  TOTAL:                   €1.82
  
REVENUE: €19.00
GROSS MARGIN: €17.18 (90%)

BREAKEVEN: 6 Pro users covers all fixed costs (€100/μήνα)
```

## Roadmap Phases

```
PHASE 1 (Weeks 1-4): MVP
  ✓ Backend skeleton + DB
  ✓ User auth (Clerk)
  ✓ CV upload + parsing
  ✓ Daily job scraper (port from existing)
  ✓ Job match computation
  ✓ Landing page + dashboard
  ✓ Manual "Apply" → opens job URL

PHASE 2 (Weeks 5-8): Paid Features
  ✓ Stripe integration
  ✓ AI cover letter generation (Claude)
  ✓ Pro tier paywall
  ✓ Email notifications
  ✓ Application tracking UI

PHASE 3 (Weeks 9-12): Growth
  ✓ One-click apply για Greenhouse/Lever
  ✓ Interview prep AI assistant
  ✓ Multi-CV support (per language)
  ✓ Referral program
  ✓ Premium tier launch

PHASE 4 (Months 4-6): Scale
  ✓ Mobile responsive polish
  ✓ Browser extension (LinkedIn Easy Apply)
  ✓ Enterprise tier
  ✓ API access
  ✓ White-label option
```
