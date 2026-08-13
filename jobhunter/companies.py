"""
Company library — έτοιμα ATS boards ανά κλάδο και περιοχή.

Ο νέος χρήστης δεν ξέρει ποια εταιρεία χρησιμοποιεί ποιο ATS. Διαλέγει κλάδους
στο onboarding και παίρνει έτοιμη λίστα. Μπορεί να προσθέσει ό,τι θέλει μετά.

Κάθε εγγραφή έχει επαληθευτεί με `python -m jobhunter doctor`. Οι εταιρείες
αλλάζουν ATS — ό,τι πέφτει, το δείχνει το doctor.
"""
from __future__ import annotations

# (provider, slug, name, industries, regions)
LIBRARY: list[dict] = [
    # ── Software / AI / infrastructure ─────────────────────────
    {"provider": "greenhouse", "slug": "datadog",    "name": "Datadog",    "industries": ["tech", "saas"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "cloudflare", "name": "Cloudflare", "industries": ["tech", "saas"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "gitlab",     "name": "GitLab",     "industries": ["tech", "saas"], "regions": ["global", "remote"]},
    {"provider": "greenhouse", "slug": "elastic",    "name": "Elastic",    "industries": ["tech", "saas"], "regions": ["global", "remote"]},
    {"provider": "greenhouse", "slug": "databricks", "name": "Databricks", "industries": ["tech", "ai", "data"], "regions": ["global"]},
    {"provider": "ashby",      "slug": "snowflake",  "name": "Snowflake",  "industries": ["tech", "data"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "figma",      "name": "Figma",      "industries": ["tech", "saas", "design"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "reddit",     "name": "Reddit",     "industries": ["tech", "media"], "regions": ["us", "remote"]},
    {"provider": "greenhouse", "slug": "discord",    "name": "Discord",    "industries": ["tech", "media"], "regions": ["us", "remote"]},
    {"provider": "greenhouse", "slug": "airtable",   "name": "Airtable",   "industries": ["tech", "saas"], "regions": ["us", "remote"]},
    {"provider": "greenhouse", "slug": "anthropic",  "name": "Anthropic",  "industries": ["tech", "ai"], "regions": ["global"]},
    {"provider": "ashby",      "slug": "openai",     "name": "OpenAI",     "industries": ["tech", "ai"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "scaleai",    "name": "Scale AI",   "industries": ["tech", "ai"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "stripe",     "name": "Stripe",     "industries": ["tech", "fintech"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "remotecom",  "name": "Remote.com", "industries": ["tech", "hr"], "regions": ["global", "remote"]},

    # ── Fintech / banking / payments ───────────────────────────
    {"provider": "greenhouse", "slug": "robinhood",  "name": "Robinhood",  "industries": ["fintech", "trading"], "regions": ["us"]},
    {"provider": "greenhouse", "slug": "chime",      "name": "Chime",      "industries": ["fintech"], "regions": ["us"]},
    {"provider": "greenhouse", "slug": "affirm",     "name": "Affirm",     "industries": ["fintech"], "regions": ["us", "remote"]},
    {"provider": "greenhouse", "slug": "marqeta",    "name": "Marqeta",    "industries": ["fintech"], "regions": ["us", "eu"]},
    {"provider": "greenhouse", "slug": "n26",        "name": "N26",        "industries": ["fintech", "banking"], "regions": ["eu"]},
    {"provider": "smartrecruiters", "slug": "Wise",  "name": "Wise",       "industries": ["fintech", "banking"], "regions": ["eu", "global"]},
    {"provider": "ashby",      "slug": "ramp",       "name": "Ramp",       "industries": ["fintech", "saas"], "regions": ["us"]},

    # ── Crypto / digital assets ────────────────────────────────
    {"provider": "greenhouse", "slug": "coinbase",   "name": "Coinbase",   "industries": ["crypto", "fintech", "trading"], "regions": ["global", "remote"]},
    {"provider": "greenhouse", "slug": "bitpanda",   "name": "Bitpanda",   "industries": ["crypto", "fintech"], "regions": ["eu"]},
    {"provider": "greenhouse", "slug": "gemini",     "name": "Gemini",     "industries": ["crypto", "trading"], "regions": ["us", "remote"]},
    {"provider": "greenhouse", "slug": "fireblocks", "name": "Fireblocks", "industries": ["crypto", "tech"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "bitgo",      "name": "BitGo",      "industries": ["crypto"], "regions": ["us", "global"]},
    {"provider": "greenhouse", "slug": "falconx",    "name": "FalconX",    "industries": ["crypto", "trading"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "binance",    "name": "Binance",    "industries": ["crypto", "trading"], "regions": ["global", "remote"]},
    {"provider": "lever",      "slug": "ledger",     "name": "Ledger",     "industries": ["crypto"], "regions": ["eu"]},

    # ── Consumer / marketplaces / delivery ─────────────────────
    {"provider": "greenhouse", "slug": "airbnb",     "name": "Airbnb",     "industries": ["consumer", "travel"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "instacart",  "name": "Instacart",  "industries": ["consumer", "retail"], "regions": ["us"]},
    {"provider": "smartrecruiters", "slug": "DeliveryHero", "name": "Delivery Hero", "industries": ["consumer", "logistics"], "regions": ["global", "eu", "apac"]},
    {"provider": "greenhouse", "slug": "cabify",     "name": "Cabify",     "industries": ["consumer", "mobility"], "regions": ["eu", "latam"]},
    {"provider": "ashby",      "slug": "nubank",     "name": "Nubank",     "industries": ["fintech", "banking"], "regions": ["latam"]},

    # ── Gaming ─────────────────────────────────────────────────
    {"provider": "greenhouse", "slug": "riotgames",  "name": "Riot Games", "industries": ["gaming"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "kaizengaming", "name": "Kaizen Gaming", "industries": ["gaming", "betting"], "regions": ["eu"]},

    # ── Education ──────────────────────────────────────────────
    {"provider": "greenhouse", "slug": "coursera",   "name": "Coursera",   "industries": ["education"], "regions": ["global", "remote"]},
    {"provider": "greenhouse", "slug": "duolingo",   "name": "Duolingo",   "industries": ["education"], "regions": ["global"]},
    {"provider": "workable",   "slug": "epignosis",  "name": "Epignosis",  "industries": ["education", "saas"], "regions": ["eu"]},

    # ── Health / logistics / marketing ─────────────────────────
    {"provider": "greenhouse", "slug": "cerebral",   "name": "Cerebral",   "industries": ["health"], "regions": ["us", "remote"]},
    {"provider": "greenhouse", "slug": "flexport",   "name": "Flexport",   "industries": ["logistics", "tech"], "regions": ["global"]},
    {"provider": "greenhouse", "slug": "klaviyo",    "name": "Klaviyo",    "industries": ["marketing", "saas"], "regions": ["global"]},

    # ── Hospitality / retail / services ────────────────────────
    {"provider": "smartrecruiters", "slug": "Accor", "name": "Accor",      "industries": ["hospitality", "travel"], "regions": ["global"]},
    {"provider": "workable",   "slug": "skroutz",    "name": "Skroutz",    "industries": ["retail", "tech"], "regions": ["eu"]},
]

ALL_INDUSTRIES: list[str] = sorted({i for c in LIBRARY for i in c["industries"]})
ALL_REGIONS: list[str] = sorted({r for c in LIBRARY for r in c["regions"]})


def pick(industries: list[str] | None = None, regions: list[str] | None = None,
         limit: int = 25) -> list[dict]:
    """Επιλογή εταιρειών ανά κλάδο/περιοχή. Χωρίς φίλτρα → οι μεγαλύτεροι boards."""
    wanted_i = {i.lower() for i in (industries or [])}
    wanted_r = {r.lower() for r in (regions or [])}

    def keep(c: dict) -> bool:
        if wanted_i and not wanted_i & {i.lower() for i in c["industries"]}:
            return False
        if wanted_r and not wanted_r & {r.lower() for r in c["regions"]}:
            return False
        return True

    chosen = [c for c in LIBRARY if keep(c)]
    if not chosen:                                    # κλάδος εκτός βιβλιοθήκης
        chosen = list(LIBRARY)
    return [{"provider": c["provider"], "slug": c["slug"], "name": c["name"]}
            for c in chosen[:limit]]


def uncovered(industries: list[str]) -> list[str]:
    """Κλάδοι που δεν έχουν εταιρείες στη βιβλιοθήκη — τους καλύπτουν τα job boards."""
    known = {i.lower() for i in ALL_INDUSTRIES}
    return [i for i in industries if i.lower() not in known]
