"""
Job sources — μόνο public JSON APIs.

Δύο είδη:
  • ATS boards  → στοχεύεις συγκεκριμένες εταιρείες (greenhouse, lever, ashby,
                  workable, smartrecruiters, recruitee)
  • Aggregators → γενικά remote/EU boards, χωρίς να ξέρεις εταιρεία
                  (remotive, arbeitnow, remoteok, jobicy)

ΔΕΝ κάνουμε scraping σε LinkedIn/Indeed: το απαγορεύουν τα ToS τους και
κινδυνεύει ο λογαριασμός σου. Ό,τι υπάρχει εδώ είναι επίσημα ανοιχτά endpoints.
"""
from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable

USER_AGENT = "JobHunter/2.0 (+personal job search assistant)"
TIMEOUT = 20

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_SALARY_RE = re.compile(
    r"(?:€|EUR|\$|USD|£|GBP)\s?(\d{2,3})[\s.,]?(\d{3})?\s?(?:k|K)?\s?(?:-|–|to)\s?"
    r"(?:€|EUR|\$|USD|£|GBP)?\s?(\d{2,3})[\s.,]?(\d{3})?\s?(?:k|K)?"
)


# ════════════════════════════════════════════════════════════════
# HTTP helpers
# ════════════════════════════════════════════════════════════════
def fetch_json(url: str, timeout: int = TIMEOUT) -> Any:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def clean_text(raw: str | None, limit: int = 8000) -> str:
    """HTML → readable plain text (χωρίς εξωτερικά parsers)."""
    if not raw:
        return ""
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</div>|</h[1-6]>", "\n", text)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:limit]


def parse_salary(text: str) -> tuple[int | None, int | None]:
    """Best-effort εξαγωγή salary range. Επιστρέφει ετήσια ποσά ή (None, None)."""
    m = _SALARY_RE.search(text or "")
    if not m:
        return None, None

    def build(major: str | None, minor: str | None) -> int | None:
        if not major:
            return None
        value = int(major + (minor or ""))
        if value < 1000:          # "50k" style
            value *= 1000
        return value if 10_000 <= value <= 500_000 else None

    return build(m.group(1), m.group(2)), build(m.group(3), m.group(4))


def _iso(value: Any) -> str | None:
    """Δέχεται epoch ms/s ή ISO string, βγάζει ISO-8601 UTC."""
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            seconds = value / 1000 if value > 1e11 else value
            return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat(timespec="seconds")
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (ValueError, OSError, OverflowError):
        return None


def _job(source: str, external_id: str, company: str, title: str, url: str,
         location: str | None = None, description: str = "", posted_at: str | None = None,
         remote: bool = False, salary: tuple[int | None, int | None] = (None, None),
         apply_email: str | None = None, raw: dict | None = None) -> dict[str, Any]:
    smin, smax = salary
    if smin is None and smax is None:
        smin, smax = parse_salary(f"{title} {description[:2000]}")
    loc = location or ""
    return {
        "source": source,
        "external_id": str(external_id),
        "company": company.strip() or "Unknown",
        "title": title.strip(),
        "location": loc.strip() or None,
        "description": description,
        "url": url,
        "posted_at": posted_at,
        "remote": bool(remote) or "remote" in loc.lower() or "anywhere" in loc.lower(),
        "salary_min": smin,
        "salary_max": smax,
        "apply_email": apply_email,
        "raw": raw or {},
    }


# ════════════════════════════════════════════════════════════════
# ATS providers — target συγκεκριμένες εταιρείες
# ════════════════════════════════════════════════════════════════
def fetch_greenhouse(slug: str, name: str) -> list[dict]:
    data = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    out = []
    for j in data.get("jobs", []):
        out.append(_job(
            "greenhouse", j.get("id"), name, j.get("title", ""), j.get("absolute_url", ""),
            location=(j.get("location") or {}).get("name"),
            description=clean_text(j.get("content")),
            posted_at=_iso(j.get("updated_at") or j.get("first_published")),
            raw={"departments": [d.get("name") for d in j.get("departments", [])]},
        ))
    return out


def fetch_lever(slug: str, name: str) -> list[dict]:
    data = fetch_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    out = []
    for j in data if isinstance(data, list) else []:
        cats = j.get("categories") or {}
        out.append(_job(
            "lever", j.get("id"), name, j.get("text", ""), j.get("hostedUrl", ""),
            location=cats.get("location"),
            description=clean_text(j.get("descriptionPlain") or j.get("description")),
            posted_at=_iso(j.get("createdAt")),
            remote=(cats.get("commitment") or "").lower() == "remote",
            raw={"team": cats.get("team"), "commitment": cats.get("commitment")},
        ))
    return out


def fetch_ashby(slug: str, name: str) -> list[dict]:
    data = fetch_json(
        f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    )
    out = []
    for j in data.get("jobs", []):
        comp = j.get("compensation") or {}
        summary = comp.get("compensationTierSummary") or ""
        out.append(_job(
            "ashby", j.get("id"), name, j.get("title", ""), j.get("jobUrl", ""),
            location=j.get("location"),
            description=clean_text(j.get("descriptionHtml") or j.get("descriptionPlain")),
            posted_at=_iso(j.get("publishedAt")),
            remote=bool(j.get("isRemote")),
            salary=parse_salary(summary),
            raw={"department": j.get("department"), "team": j.get("team")},
        ))
    return out


def fetch_workable(slug: str, name: str) -> list[dict]:
    data = fetch_json(f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
    out = []
    for j in data.get("jobs", []):
        loc = ", ".join(p for p in [j.get("city"), j.get("country")] if p)
        out.append(_job(
            "workable", j.get("shortcode") or j.get("id"), name, j.get("title", ""),
            j.get("url") or j.get("application_url", ""),
            location=loc,
            description=clean_text(j.get("description")),
            posted_at=_iso(j.get("published_on") or j.get("created_at")),
            remote=bool(j.get("telecommuting")),
            raw={"department": j.get("department")},
        ))
    return out


def fetch_smartrecruiters(slug: str, name: str) -> list[dict]:
    data = fetch_json(
        f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100"
    )
    out = []
    for j in data.get("content", []):
        loc_obj = j.get("location") or {}
        loc = ", ".join(p for p in [loc_obj.get("city"), loc_obj.get("country")] if p)
        out.append(_job(
            "smartrecruiters", j.get("id"), name, j.get("name", ""),
            f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}",
            location=loc,
            description=clean_text(json.dumps(j.get("jobAd") or {}, ensure_ascii=False)),
            posted_at=_iso(j.get("releasedDate")),
            remote=bool(loc_obj.get("remote")),
        ))
    return out


def fetch_recruitee(slug: str, name: str) -> list[dict]:
    data = fetch_json(f"https://{slug}.recruitee.com/api/offers/")
    out = []
    for j in data.get("offers", []):
        out.append(_job(
            "recruitee", j.get("id"), name, j.get("title", ""), j.get("careers_url", ""),
            location=j.get("location") or j.get("city"),
            description=clean_text(j.get("description")),
            posted_at=_iso(j.get("published_at")),
            remote=bool(j.get("remote")),
        ))
    return out


ATS_PROVIDERS: dict[str, Callable[[str, str], list[dict]]] = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "workable": fetch_workable,
    "smartrecruiters": fetch_smartrecruiters,
    "recruitee": fetch_recruitee,
}


# ════════════════════════════════════════════════════════════════
# Aggregators — δουλεύουν χωρίς λίστα εταιρειών
# ════════════════════════════════════════════════════════════════
def fetch_remotive(query: str = "") -> list[dict]:
    url = "https://remotive.com/api/remote-jobs?limit=200"
    if query:
        url += "&search=" + urllib.parse.quote(query)
    data = fetch_json(url)
    return [
        _job("remotive", j.get("id"), j.get("company_name", ""), j.get("title", ""), j.get("url", ""),
             location=j.get("candidate_required_location"),
             description=clean_text(j.get("description")),
             posted_at=_iso(j.get("publication_date")),
             remote=True,
             salary=parse_salary(j.get("salary") or ""))
        for j in data.get("jobs", [])
    ]


def fetch_arbeitnow(query: str = "") -> list[dict]:
    data = fetch_json("https://www.arbeitnow.com/api/job-board-api")
    out = []
    for j in data.get("data", []):
        out.append(_job(
            "arbeitnow", j.get("slug"), j.get("company_name", ""), j.get("title", ""),
            j.get("url", ""),
            location=j.get("location"),
            description=clean_text(j.get("description")),
            posted_at=_iso(j.get("created_at")),
            remote=bool(j.get("remote")),
            raw={"tags": j.get("tags", [])},
        ))
    return out


def fetch_remoteok(query: str = "") -> list[dict]:
    data = fetch_json("https://remoteok.com/api")
    out = []
    for j in data if isinstance(data, list) else []:
        if not j.get("id") or not j.get("position"):
            continue  # το πρώτο item είναι legal notice
        out.append(_job(
            "remoteok", j.get("id"), j.get("company", ""), j.get("position", ""),
            j.get("url", ""),
            location=j.get("location") or "Remote",
            description=clean_text(j.get("description")),
            posted_at=_iso(j.get("date")),
            remote=True,
            salary=(j.get("salary_min") or None, j.get("salary_max") or None),
            raw={"tags": j.get("tags", [])},
        ))
    return out


def fetch_jobicy(query: str = "") -> list[dict]:
    url = "https://jobicy.com/api/v2/remote-jobs?count=100"
    data = fetch_json(url)
    return [
        _job("jobicy", j.get("id"), j.get("companyName", ""), j.get("jobTitle", ""), j.get("url", ""),
             location=j.get("jobGeo"),
             description=clean_text(j.get("jobDescription") or j.get("jobExcerpt")),
             posted_at=_iso(j.get("pubDate")),
             remote=True,
             salary=(j.get("annualSalaryMin") or None, j.get("annualSalaryMax") or None))
        for j in data.get("jobs", [])
    ]


def fetch_himalayas(query: str = "") -> list[dict]:
    data = fetch_json("https://himalayas.app/jobs/api?limit=100")
    out = []
    for j in data.get("jobs", []):
        restrictions = j.get("locationRestrictions") or []
        location = ", ".join(restrictions) if restrictions else "Worldwide"
        out.append(_job(
            "himalayas", j.get("guid") or j.get("applicationLink", ""),
            j.get("companyName", ""), j.get("title", ""),
            j.get("applicationLink", ""),
            location=location,
            description=clean_text(j.get("description") or j.get("excerpt")),
            posted_at=_iso(j.get("pubDate") or j.get("publishedDate")),
            remote=True,
            salary=(j.get("minSalary") or None, j.get("maxSalary") or None),
            raw={"categories": j.get("categories", [])},
        ))
    return out


def fetch_workingnomads(query: str = "") -> list[dict]:
    data = fetch_json("https://www.workingnomads.com/api/exposed_jobs/")
    out = []
    for j in data if isinstance(data, list) else []:
        url = j.get("url", "")
        out.append(_job(
            "workingnomads", url.rsplit("/", 1)[-1] or url, j.get("company_name", ""),
            j.get("title", ""), url,
            location=j.get("location") or "Worldwide",
            description=clean_text(j.get("description")),
            posted_at=_iso(j.get("pub_date")),
            remote=True,
            raw={"category": j.get("category_name"), "tags": j.get("tags")},
        ))
    return out


AGGREGATORS: dict[str, Callable[[str], list[dict]]] = {
    "remotive": fetch_remotive,
    "arbeitnow": fetch_arbeitnow,
    "remoteok": fetch_remoteok,
    "jobicy": fetch_jobicy,
    "himalayas": fetch_himalayas,
    "workingnomads": fetch_workingnomads,
}


# ════════════════════════════════════════════════════════════════
# Orchestration
# ════════════════════════════════════════════════════════════════
def fetch_all(targets: list[dict], boards: list[str], query: str = "",
              on_progress: Callable[[str, int, str], None] | None = None,
              max_workers: int = 12) -> tuple[list[dict], list[str]]:
    """
    targets: [{"provider": "greenhouse", "slug": "bitpanda", "name": "Bitpanda"}, ...]
    boards:  ["remotive", "arbeitnow", ...]

    Returns (jobs, errors). Ένα σπασμένο source δεν ρίχνει ποτέ το run.
    """
    jobs: list[dict] = []
    errors: list[str] = []
    tasks: dict[Any, str] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for t in targets:
            fetcher = ATS_PROVIDERS.get(t.get("provider", ""))
            if not fetcher:
                errors.append(f"{t.get('name')}: άγνωστος provider '{t.get('provider')}'")
                continue
            label = f"{t['name']} ({t['provider']})"
            tasks[pool.submit(fetcher, t["slug"], t["name"])] = label

        for board in boards:
            fetcher_agg = AGGREGATORS.get(board)
            if not fetcher_agg:
                errors.append(f"άγνωστο board '{board}'")
                continue
            tasks[pool.submit(fetcher_agg, query)] = board

        for fut in as_completed(tasks):
            label = tasks[fut]
            try:
                result = fut.result()
            except urllib.error.HTTPError as e:
                errors.append(f"{label}: HTTP {e.code}")
                if on_progress:
                    on_progress(label, 0, f"HTTP {e.code}")
                continue
            except Exception as e:                      # network/JSON/whatever
                errors.append(f"{label}: {type(e).__name__}: {e}")
                if on_progress:
                    on_progress(label, 0, str(e))
                continue
            jobs.extend(result)
            if on_progress:
                on_progress(label, len(result), "ok")

    # De-dup μέσα στο ίδιο run (source+external_id)
    seen: set[tuple[str, str]] = set()
    unique = []
    for j in jobs:
        key = (j["source"], j["external_id"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(j)
    return unique, errors
