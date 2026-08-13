# JobHunter Frontend

Next.js 14 (App Router) + Tailwind + Clerk auth.

## Local setup

```bash
# 1. Install
npm install

# 2. Env vars
cp .env.example .env.local
# Edit με τα Clerk keys

# 3. Run dev server
npm run dev
```

http://localhost:3000

## Structure

```
app/
├── layout.tsx           Root + ClerkProvider
├── globals.css          Tailwind + theme tokens
├── page.tsx             Landing (Hero → Features → Pricing → FAQ)
├── dashboard/
│   └── page.tsx         Main user surface (post-login)
├── jobs/                TODO: full job list + filters
├── applications/        TODO: tracking page
├── settings/            TODO: CV upload, preferences, billing
└── billing/             TODO: Stripe checkout link

components/              shadcn/ui components (will add)
lib/                     API client, hooks, utilities
```

## Deployment

```bash
# Vercel — zero-config
vercel deploy
```

## Phase 1 status

- ✅ Landing page (responsive, Tailwind)
- ✅ Auth wiring (Clerk)
- ✅ Dashboard skeleton
- ⏳ Jobs page με actual matches API integration
- ⏳ Settings: CV upload UI
- ⏳ Stripe checkout flow
- ⏳ Mobile polish
