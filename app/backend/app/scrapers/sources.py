"""
Job source fetchers — Greenhouse, Lever, Workable, Ashby.
All use public JSON APIs (legal, no auth required).
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx

log = logging.getLogger(__name__)


class JobResult:
    """Normalized job representation across all sources."""
    def __init__(self, source: str, external_id: str, company: str,
                 title: str, location: str | None, description: str | None,
                 url: str, posted_at: datetime | None = None,
                 salary_min: int | None = None, salary_max: int | None = None,
                 remote: bool = False, raw: dict | None = None):
        self.source = source
        self.external_id = external_id
        self.company = company
        self.title = title
        self.location = location
        self.description = description
        self.url = url
        self.posted_at = posted_at
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.remote = remote
        self.raw = raw or {}


# ════════════════════════════════════════════════════════════════
# GREENHOUSE
# ════════════════════════════════════════════════════════════════
async def fetch_greenhouse(client: httpx.AsyncClient, company_id: str,
                            company_name: str) -> list[JobResult]:
    """Public board API: boards-api.greenhouse.io/v1/boards/{id}/jobs"""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_id}/jobs?content=true"
    try:
        r = await client.get(url, timeout=15.0)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(f"Greenhouse fetch failed για {company_id}: {e}")
        return []

    jobs = []
    for j in data.get("jobs", []):
        location_name = (j.get("location") or {}).get("name", "")
        is_remote = "remote" in location_name.lower()
        posted_at = None
        if j.get("updated_at"):
            try:
                posted_at = datetime.fromisoformat(j["updated_at"].replace("Z", "+00:00"))
            except Exception:
                pass

        jobs.append(JobResult(
            source="greenhouse",
            external_id=str(j.get("id", "")),
            company=company_name,
            title=j.get("title", ""),
            location=location_name,
            description=j.get("content", ""),
            url=j.get("absolute_url", ""),
            posted_at=posted_at,
            remote=is_remote,
            raw=j,
        ))
    return jobs


# ════════════════════════════════════════════════════════════════
# LEVER
# ════════════════════════════════════════════════════════════════
async def fetch_lever(client: httpx.AsyncClient, company_id: str,
                       company_name: str) -> list[JobResult]:
    """Public postings API: api.lever.co/v0/postings/{id}?mode=json"""
    url = f"https://api.lever.co/v0/postings/{company_id}?mode=json"
    try:
        r = await client.get(url, timeout=15.0)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(f"Lever fetch failed για {company_id}: {e}")
        return []

    if not isinstance(data, list):
        return []

    jobs = []
    for j in data:
        location = (j.get("categories") or {}).get("location", "")
        is_remote = "remote" in location.lower()
        posted_at = None
        if j.get("createdAt"):
            try:
                posted_at = datetime.fromtimestamp(
                    j["createdAt"] / 1000, tz=timezone.utc,
                )
            except Exception:
                pass

        jobs.append(JobResult(
            source="lever",
            external_id=j.get("id", ""),
            company=company_name,
            title=j.get("text", ""),
            location=location,
            description=j.get("descriptionPlain", ""),
            url=j.get("hostedUrl", ""),
            posted_at=posted_at,
            remote=is_remote,
            raw=j,
        ))
    return jobs


# ════════════════════════════════════════════════════════════════
# WORKABLE
# ════════════════════════════════════════════════════════════════
async def fetch_workable(client: httpx.AsyncClient, company_id: str,
                          company_name: str) -> list[JobResult]:
    """Public API: apply.workable.com/api/v3/accounts/{id}/jobs"""
    url = f"https://apply.workable.com/api/v3/accounts/{company_id}/jobs"
    try:
        r = await client.get(url, timeout=15.0)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning(f"Workable fetch failed για {company_id}: {e}")
        return []

    jobs = []
    for j in data.get("results", []):
        location_parts = [j.get("city"), j.get("country")]
        location = ", ".join(p for p in location_parts if p) or "Remote"
        posted_at = None
        if j.get("published_at"):
            try:
                posted_at = datetime.fromisoformat(j["published_at"].replace("Z", "+00:00"))
            except Exception:
                pass

        jobs.append(JobResult(
            source="workable",
            external_id=j.get("shortcode") or j.get("id", ""),
            company=company_name,
            title=j.get("title", ""),
            location=location,
            description=j.get("description", ""),
            url=j.get("url") or j.get("application_url", ""),
            posted_at=posted_at,
            remote=j.get("telecommuting", False),
            raw=j,
        ))
    return jobs


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever":      fetch_lever,
    "workable":   fetch_workable,
}


# ════════════════════════════════════════════════════════════════
# COMPANY REGISTRY
# ════════════════════════════════════════════════════════════════
# Format: company_name -> (provider, identifier)
# Add new companies by inspecting their careers page source.
COMPANIES = {
    # Crypto exchanges (verified working)
    "Binance":      ("greenhouse", "binance"),
    "Kraken":       ("greenhouse", "krakendigitalassetexchange"),
    "Coinbase":     ("greenhouse", "coinbase"),
    "Gemini":       ("greenhouse", "gemini"),
    "Bitstamp":     ("greenhouse", "bitstamp"),
    "FalconX":      ("greenhouse", "falconx"),
    "Bitpanda":     ("greenhouse", "bitpanda"),

    # Custodians + infrastructure
    "BitGo":        ("greenhouse", "bitgo"),
    "Anchorage":    ("greenhouse", "anchoragedigital"),
    "Fireblocks":   ("greenhouse", "fireblocks"),

    # Fintech / EU
    "N26":          ("greenhouse", "n26"),
    "Revolut":      ("greenhouse", "revolut"),
    "Wise":         ("greenhouse", "wise"),
    "Ebury":        ("greenhouse", "ebury"),

    # Spain / Madrid hubs
    "Cabify":       ("greenhouse", "cabify"),
    "Glovo":        ("greenhouse", "glovo"),
}


async def scrape_all() -> list[JobResult]:
    """Run all configured scrapers in parallel, return aggregated results."""
    async with httpx.AsyncClient(
        headers={"User-Agent": "JobHunter/1.0 (jobhunter.app)"},
        follow_redirects=True,
    ) as client:
        tasks = []
        for company_name, (provider, cid) in COMPANIES.items():
            fetcher = FETCHERS.get(provider)
            if fetcher:
                tasks.append(fetcher(client, cid, company_name))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs = []
    for r in results:
        if isinstance(r, Exception):
            log.error(f"Scraper error: {r}")
            continue
        all_jobs.extend(r)

    log.info(f"Scraped {len(all_jobs)} jobs across {len(COMPANIES)} companies")
    return all_jobs
