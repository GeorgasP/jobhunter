/*
 * Πηγές αγγελιών — μόνο δημόσια JSON APIs.
 *
 * Το fetch γίνεται από τον service worker, οπότε δεν μας αφορά CORS ούτε το
 * CSP καμίας σελίδας. Καμία σύνδεση με LinkedIn/Indeed: το απαγορεύουν τα ToS
 * τους και μπλοκάρουν λογαριασμούς.
 */

const UA_TIMEOUT = 20000;

async function request(url, options = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), UA_TIMEOUT);
  try {
    const res = await fetch(url, { signal: ctrl.signal, ...options });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res;
  } finally {
    clearTimeout(timer);
  }
}

const getJSON = async (url) =>
  (await request(url, { headers: { accept: "application/json" } })).json();

const getText = async (url) => (await request(url)).text();

const postJSON = async (url, body) =>
  (await request(url, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify(body),
  })).json();

// Ο service worker δεν έχει DOMParser — τα RSS τα διαβάζουμε με regex.
const NAMED_ENTITIES = {
  amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ",
  mdash: "\u2014", ndash: "\u2013", minus: "\u2212", hellip: "\u2026",
  bull: "\u2022", middot: "\u00B7", lsquo: "\u2018", rsquo: "\u2019",
  ldquo: "\u201C", rdquo: "\u201D", euro: "\u20AC", pound: "\u00A3",
  yen: "\u00A5", cent: "\u00A2", deg: "\u00B0", trade: "\u2122",
  copy: "\u00A9", reg: "\u00AE", times: "\u00D7",
};

const decodeEntities = (s) => (s || "")
  .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
  .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(Number(dec)))
  .replace(/&([a-z]+\d*);/gi, (whole, name) => NAMED_ENTITIES[name.toLowerCase()] ?? whole);

const tagValue = (xml, tag) => {
  const m = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`).exec(xml);
  if (!m) return "";
  return decodeEntities(m[1].replace(/^<!\[CDATA\[|\]\]>$/g, "").trim());
};

const rssItems = (xml) => [...xml.matchAll(/<item[^>]*>([\s\S]*?)<\/item>/g)].map((m) => m[1]);

/**
 * Το Greenhouse στέλνει το HTML ΔΙΠΛΑ κωδικοποιημένο (&lt;div&gt;). Μία πάσα
 * αφαιρεί tags που δεν έχουν εμφανιστεί ακόμη και μετά τα αποκαλύπτει, οπότε
 * το markup έμενε μέσα στην περιγραφή. Επαναλαμβάνουμε ώσπου να σταθεροποιηθεί.
 */
const stripHtml = (raw, limit = 6000) => {
  if (!raw) return "";
  let text = String(raw);

  for (let pass = 0; pass < 3; pass++) {
    const stripped = text
      .replace(/<(script|style)[\s\S]*?<\/\1>/gi, " ")
      .replace(/<br\s*\/?>|<\/p>|<\/li>|<\/div>|<\/h[1-6]>|<\/tr>/gi, "\n")
      .replace(/<[^>]+>/g, " ");
    const decoded = decodeEntities(stripped);
    if (decoded === text) break;
    text = decoded;
  }

  return text
    .replace(/[ \t]+/g, " ")
    .replace(/\n[ \t]+/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
    .slice(0, limit);
};

/** Το Workday δίνει «Posted Today» / «Posted 5 Days Ago» αντί για ημερομηνία. */
function relativeDate(text) {
  if (!text) return null;
  const t = String(text).toLowerCase();
  const days = /today/.test(t) ? 0
    : /yesterday/.test(t) ? 1
    : (Number((/(\d+)\+?\s*days?/.exec(t) || [])[1])
       || Number((/(\d+)\+?\s*months?/.exec(t) || [])[1]) * 30) || null;
  if (days === null) return null;
  return new Date(Date.now() - days * 86400000).toISOString();
}

const iso = (v) => {
  if (!v) return null;
  try {
    const d = typeof v === "number" ? new Date(v > 1e11 ? v : v * 1000) : new Date(v);
    return isNaN(d) ? null : d.toISOString();
  } catch { return null; }
};

// Αποθηκεύουμε τον ISO κωδικό (EUR/USD/…) ώστε να γίνεται μετατροπή· το
// σύμβολο για την εμφάνιση βγαίνει από αυτόν.
const CURRENCY = {
  "€": "EUR", eur: "EUR", "$": "USD", usd: "USD", "£": "GBP", gbp: "GBP",
  "zł": "PLN", pln: "PLN", chf: "CHF", sek: "SEK", kr: "SEK",
  "₹": "INR", inr: "INR", cad: "CAD", aud: "AUD", "¥": "JPY", jpy: "JPY",
  brl: "BRL", "r$": "BRL", try: "TRY", "₺": "TRY", czk: "CZK", huf: "HUF",
  ron: "RON", dkk: "DKK", nok: "NOK", ils: "ILS", "₪": "ILS", aed: "AED",
  sgd: "SGD", zar: "ZAR", mxn: "MXN",
};

const symbolFor = (code) => CURRENCY[String(code || "").toLowerCase()] || null;

const SALARY_RE = /(€|EUR|\$|USD|£|GBP|PLN|CHF|SEK|₹|INR)\s?(\d{1,3})[\s.,]?(\d{3})?\s?(k)?\s?(?:-|–|—|to|až)\s?(?:€|EUR|\$|USD|£|GBP|PLN|CHF|SEK|₹|INR)?\s?(\d{1,3})[\s.,]?(\d{3})?\s?(k)?/i;

/**
 * Returns [min, max, currency, period]. Χωρίς τη συχνότητα, το «3.500-5.500»
 * ενός μηνιαίου μισθού διαβάζεται σαν ετήσιος και παραπλανά.
 */
export function parseSalary(text) {
  const source = text || "";
  const m = SALARY_RE.exec(source);
  if (!m) return [null, null, null, null];

  // Η περίοδος πρέπει να βρεθεί ΠΡΙΝ τους αριθμούς: «$25 - $40 per hour»
  // είναι είκοσι πέντε δολάρια την ώρα, όχι είκοσι πέντε χιλιάδες.
  const after = source.slice(m.index, m.index + m[0].length + 60).toLowerCase();
  const period = /\/\s*(hr|hour)|per hour|hourly|an hour/.test(after) ? "hour"
    : /\/\s*(mo|month)|per month|monthly|a month|μηνια/.test(after) ? "month"
    : /per day|daily|\/\s*day|a day/.test(after) ? "day"
    : /per week|weekly|\/\s*week|a week/.test(after) ? "week"
    : "year";

  // Ανά περίοδο αλλάζει και το τι είναι λογικό ποσό, και το αν το «45»
  // σημαίνει σαράντα πέντε χιλιάδες.
  const RANGE = { hour: [3, 2000], day: [20, 5000], week: [50, 20000],
                  month: [200, 60000], year: [3000, 900000] };
  const [low, high] = RANGE[period];
  const shortForm = period === "year" || period === "month";
  const kiloAnywhere = Boolean(m[4] || m[7]);

  const build = (major, minor, kilo) => {
    if (!major) return null;
    let v = parseInt(major + (minor || ""), 10);
    if (kilo || kiloAnywhere || (shortForm && !minor && v < 100)) v *= 1000;
    return v >= low && v <= high ? v : null;
  };

  const currency = CURRENCY[(m[1] || "").toLowerCase()] || null;
  return [build(m[2], m[3], m[4]), build(m[5], m[6], m[7]), currency, period];
}

function job(source, externalId, company, title, url, opts = {}) {
  const location = opts.location || "";
  let [smin, smax, currency, period] = opts.salary || [null, null, null, null];
  if (smin == null && smax == null) {
    // Ο μισθός συχνά αναφέρεται βαθιά μέσα στην αγγελία, όχι στην αρχή.
    [smin, smax, currency, period] = parseSalary(`${title} ${opts.description || ""}`);
  }
  return {
    id: `${source}:${externalId}`,
    source, company: (company || "Unknown").trim(), title: (title || "").trim(),
    location: location.trim(), description: opts.description || "", url,
    postedAt: opts.postedAt || null,
    remote: Boolean(opts.remote) || /remote|anywhere|worldwide/i.test(location),
    salaryMin: smin, salaryMax: smax,
    salaryCurrency: currency || opts.currency || null,
    salaryPeriod: period || "year",
    lastSeen: new Date().toISOString(),
  };
}

/* ── ATS providers: στοχευμένες εταιρείες ─────────────────── */
export const ATS = {
  /**
   * Workday: το χρησιμοποιούν οι περισσότερες μεγάλες εταιρείες.
   * slug = "tenant/datacenter/site", π.χ. "nvidia/wd5/NVIDIAExternalCareerSite"
   * (φαίνεται στο URL της σελίδας καριέρας τους).
   */
  async workday(slug, name) {
    const [tenant, dc = "wd1", site] = slug.split("/");
    const base = `https://${tenant}.${dc}.myworkdayjobs.com`;
    const endpoint = `${base}/wday/cxs/${tenant}/${site}/jobs`;
    // Το Workday απορρίπτει limit > 20, οπότε ζητάμε πέντε σελίδες παράλληλα.
    const pages = await Promise.all([0, 20, 40, 60, 80].map((offset) =>
      postJSON(endpoint, { appliedFacets: {}, limit: 20, offset, searchText: "" })
        .catch(() => ({ jobPostings: [] }))));

    return pages.flatMap((d) => d.jobPostings || []).map((j) => {
      // Όταν λέει «5 Locations» δεν μας λέει τίποτα — και με ενεργό φίλτρο
      // τοποθεσίας θα κοβόταν η αγγελία. Η αληθινή πόλη είναι μέσα στο path:
      // /job/US-CA-Santa-Clara/Software-Engineer… → «Santa Clara, US»
      let location = j.locationsText || "";
      if (/^\s*\d+\s+locations?\s*$/i.test(location)) {
        const segment = (j.externalPath || "").split("/")[2] || "";
        const parts = segment.split("-").filter(Boolean);
        location = parts.length > 1
          ? `${parts.slice(1).join(" ")}, ${parts[0]}`
          : "";
      }
      return job("workday", (j.bulletFields || [])[0] || j.externalPath, name, j.title,
        `${base}/${site}${j.externalPath}`, {
        location,
        postedAt: relativeDate(j.postedOn),
        remote: /remote/i.test(`${j.locationsText} ${j.externalPath}`),
      });
    });
  },

  async teamtailor(slug, name) {
    const d = await getJSON(`https://${slug}.teamtailor.com/jobs.json`);
    return (d.items || []).map((j) => job("teamtailor", j.id, name || d.title, j.title, j.url, {
      description: stripHtml(j.content_html),
      postedAt: iso(j.date_published),
    }));
  },

  async breezy(slug, name) {
    const d = await getJSON(`https://${slug}.breezy.hr/json`);
    return (Array.isArray(d) ? d : []).map((j) => job("breezy", j.id, name, j.name,
      `https://${slug}.breezy.hr/p/${j.id}`, {
      location: [j.location?.city, j.location?.country?.name].filter(Boolean).join(", "),
      description: stripHtml(j.description),
      postedAt: iso(j.published_date || j.creation_date),
      remote: Boolean(j.location?.is_remote),
    }));
  },

  async greenhouse(slug, name) {
    const d = await getJSON(`https://boards-api.greenhouse.io/v1/boards/${slug}/jobs?content=true`);
    return (d.jobs || []).map((j) => job("greenhouse", j.id, name, j.title, j.absolute_url, {
      location: j.location?.name, description: stripHtml(j.content),
      postedAt: iso(j.updated_at || j.first_published),
    }));
  },
  async lever(slug, name) {
    const d = await getJSON(`https://api.lever.co/v0/postings/${slug}?mode=json`);
    return (Array.isArray(d) ? d : []).map((j) => job("lever", j.id, name, j.text, j.hostedUrl, {
      location: j.categories?.location,
      description: stripHtml(j.descriptionPlain || j.description),
      postedAt: iso(j.createdAt),
      remote: /remote/i.test(j.categories?.commitment || ""),
    }));
  },
  async ashby(slug, name) {
    const d = await getJSON(`https://api.ashbyhq.com/posting-api/job-board/${slug}?includeCompensation=true`);
    return (d.jobs || []).map((j) => job("ashby", j.id, name, j.title, j.jobUrl, {
      location: j.location, description: stripHtml(j.descriptionHtml || j.descriptionPlain),
      postedAt: iso(j.publishedAt), remote: j.isRemote,
      salary: parseSalary(j.compensation?.compensationTierSummary || ""),
    }));
  },
  async workable(slug, name) {
    const d = await getJSON(`https://apply.workable.com/api/v1/widget/accounts/${slug}?details=true`);
    return (d.jobs || []).map((j) => job("workable", j.shortcode || j.id, name, j.title,
      j.url || j.application_url, {
      location: [j.city, j.country].filter(Boolean).join(", "),
      description: stripHtml(j.description),
      postedAt: iso(j.published_on || j.created_at), remote: j.telecommuting,
    }));
  },
  async smartrecruiters(slug, name) {
    const d = await getJSON(`https://api.smartrecruiters.com/v1/companies/${slug}/postings?limit=100`);
    return (d.content || []).map((j) => job("smartrecruiters", j.id, name, j.name,
      `https://jobs.smartrecruiters.com/${slug}/${j.id}`, {
      location: [j.location?.city, j.location?.country].filter(Boolean).join(", "),
      description: stripHtml(JSON.stringify(j.jobAd || {})),
      postedAt: iso(j.releasedDate), remote: j.location?.remote,
    }));
  },
  async recruitee(slug, name) {
    const d = await getJSON(`https://${slug}.recruitee.com/api/offers/`);
    return (d.offers || []).map((j) => job("recruitee", j.id, name, j.title, j.careers_url, {
      location: j.location || j.city, description: stripHtml(j.description),
      postedAt: iso(j.published_at), remote: j.remote,
    }));
  },
};

/* ── Aggregators: δουλεύουν χωρίς λίστα εταιρειών ──────────── */
export const BOARDS = {
  /** The Muse — δεκάδες χιλιάδες θέσεις, όχι μόνο remote, σε όλο τον κόσμο. */
  async themuse(query) {
    const pages = await Promise.all([0, 1, 2].map((p) =>
      getJSON(`https://www.themuse.com/api/public/jobs?page=${p}&descending=true`)
        .catch(() => ({ results: [] }))));
    return pages.flatMap((d) => d.results || []).map((j) => job("themuse", j.id,
      j.company?.name, j.name, j.refs?.landing_page || "", {
      location: (j.locations || []).map((l) => l.name).join(", "),
      description: stripHtml(j.contents),
      postedAt: iso(j.publication_date),
      remote: (j.locations || []).some((l) => /flexible|remote/i.test(l.name)),
    })).filter((j) => j.url);
  },

  /** We Work Remotely — RSS, ο τίτλος έχει μορφή «Εταιρεία: Θέση». */
  async weworkremotely() {
    const xml = await getText("https://weworkremotely.com/remote-jobs.rss");
    return rssItems(xml).map((item) => {
      const full = tagValue(item, "title");
      const split = full.indexOf(":");
      const company = split > 0 ? full.slice(0, split).trim() : "";
      const title = split > 0 ? full.slice(split + 1).trim() : full;
      const url = tagValue(item, "link") || tagValue(item, "guid");
      return job("weworkremotely", url.split("/").pop() || url, company, title, url, {
        location: tagValue(item, "region") || "Remote",
        description: stripHtml(decodeEntities(tagValue(item, "description"))),
        postedAt: iso(tagValue(item, "pubDate")),
        remote: true,
        raw: { category: tagValue(item, "category"), type: tagValue(item, "type") },
      });
    }).filter((j) => j.url && j.title);
  },

  /** Cryptocurrency Jobs — RSS, τίτλος «Θέση at Εταιρεία». */
  async cryptojobs() {
    const xml = await getText("https://cryptocurrencyjobs.co/index.xml");
    return rssItems(xml).map((item) => {
      const full = tagValue(item, "title");
      const at = full.lastIndexOf(" at ");
      const url = tagValue(item, "link") || tagValue(item, "guid");
      return job("cryptojobs", url.split("/").filter(Boolean).pop() || url,
        at > 0 ? full.slice(at + 4).trim() : "", at > 0 ? full.slice(0, at).trim() : full, url, {
        location: "Remote",
        description: stripHtml(decodeEntities(tagValue(item, "description"))),
        postedAt: iso(tagValue(item, "pubDate")),
        remote: true,
      });
    }).filter((j) => j.url && j.title);
  },

  /** Landing.jobs — ευρωπαϊκές τεχνολογικές θέσεις· η εταιρεία είναι στο URL. */
  async landingjobs() {
    const d = await getJSON("https://landing.jobs/api/v1/jobs");
    return (Array.isArray(d) ? d : []).map((j) => {
      const parts = String(j.url || "").split("/");
      const company = parts[parts.indexOf("at") + 1] || "";
      return job("landingjobs", j.id, company.replace(/-/g, " "), j.title, j.url, {
        location: (j.locations || []).map((l) => l.city || l.name || l).filter(Boolean).join(", "),
        description: stripHtml([j.role_description, j.main_requirements].filter(Boolean).join("\n")),
        postedAt: iso(j.published_at),
        remote: Boolean(j.remote),
        salary: [j.gross_salary_low || null, j.gross_salary_high || null,
                 symbolFor(j.currency_code), "year"],
      });
    }).filter((j) => j.url && j.title);
  },

  async remotive(query) {
    const url = "https://remotive.com/api/remote-jobs?limit=200" + (query ? `&search=${encodeURIComponent(query)}` : "");
    const d = await getJSON(url);
    return (d.jobs || []).map((j) => job("remotive", j.id, j.company_name, j.title, j.url, {
      location: j.candidate_required_location, description: stripHtml(j.description),
      postedAt: iso(j.publication_date), remote: true, salary: parseSalary(j.salary || ""),
    }));
  },
  async arbeitnow() {
    // Η πρώτη σελίδα δίνει 175 αγγελίες, αλλά υπάρχουν άλλες έξι από πίσω —
    // 739 μοναδικές συνολικά. Είναι και η μόνη μας πηγή με πραγματικές θέσεις
    // εκτός γραφείου (νοσηλευτές, οδηγοί, τεχνίτες), οπότε αξίζει τα αιτήματα.
    const seen = new Set();
    const out = [];
    for (let page = 1; page <= 7; page++) {
      let d;
      try {
        d = await getJSON(`https://www.arbeitnow.com/api/job-board-api?page=${page}`);
      } catch { break; }
      const rows = d.data || [];
      if (!rows.length) break;
      let fresh = 0;
      for (const j of rows) {
        if (seen.has(j.slug)) continue;
        seen.add(j.slug);
        fresh++;
        out.push(job("arbeitnow", j.slug, j.company_name, j.title, j.url, {
          location: j.location, description: stripHtml(j.description),
          postedAt: iso(j.created_at), remote: j.remote,
        }));
      }
      if (!fresh) break;
    }
    return out;
  },

  /*
   * Adzuna — η μόνη πηγή που φέρνει ολόκληρη την αγορά μιας χώρας, όχι μόνο
   * τεχνολογία: νοσηλευτές, οδηγούς, μάγειρες, τεχνίτες. Καλύπτει 44 χώρες,
   * ανάμεσά τους την Ελλάδα.
   *
   * Θέλει κλειδί του ίδιου του χρήστη, δωρεάν από το developer.adzuna.com.
   * Χωρίς κλειδί βγαίνει σιωπηλά από τη σάρωση — δεν χαλάει τίποτα.
   *
   * Τα όριά τους είναι 25 αιτήματα/λεπτό και 250/ημέρα: με δύο σαρώσεις την
   * ημέρα και τρεις χώρες μένουμε πολύ χαμηλά.
   */
  async adzuna(query, opts = {}) {
    const cfg = (opts && opts.adzuna) || {};
    if (!cfg.appId || !cfg.appKey) return [];

    const countries = (cfg.countries || []).map((c) => c.trim().toLowerCase())
      .filter(Boolean).slice(0, 3);
    if (!countries.length) return [];

    const CURRENCY_OF = {
      gb: "GBP", us: "USD", ca: "CAD", au: "AUD", nz: "NZD", in: "INR", sg: "SGD",
      za: "ZAR", ch: "CHF", pl: "PLN", se: "SEK", no: "NOK", dk: "DKK", cz: "CZK",
      hu: "HUF", ro: "RON", tr: "TRY", br: "BRL", mx: "MXN", ar: "ARS", cl: "CLP",
      co: "COP", jp: "JPY", kr: "KRW", cn: "CNY", ae: "AED", ru: "RUB",
    };
    const out = [];

    for (const country of countries) {
      const currency = CURRENCY_OF[country] || "EUR";
      const params = new URLSearchParams({
        app_id: cfg.appId, app_key: cfg.appKey,
        results_per_page: "50", max_days_old: "30", content_type: "application/json",
      });
      if (query) params.set("what", query);

      for (let page = 1; page <= 2; page++) {
        let d;
        try {
          d = await getJSON(
            `https://api.adzuna.com/v1/api/jobs/${country}/search/${page}?${params}`);
        } catch { break; }
        const rows = d.results || [];
        if (!rows.length) break;
        for (const j of rows) {
          out.push(job("adzuna", j.id, j.company?.display_name, j.title, j.redirect_url, {
            location: j.location?.display_name || country.toUpperCase(),
            description: stripHtml(j.description),
            postedAt: iso(j.created),
            salary: [j.salary_min || null, j.salary_max || null, currency, "year"],
          }));
        }
        if (rows.length < 50) break;
      }
    }
    return out;
  },

  /* Βρετανική αγορά με μισθό και επίπεδο εμπειρίας δηλωμένα σε κάθε αγγελία —
     δύο πεδία που οι περισσότερες πηγές τα αφήνουν κενά. */
  async devitjobs() {
    const d = await getJSON("https://devitjobs.uk/api/jobsLight");
    return (Array.isArray(d) ? d : []).filter((j) => j.name && j.jobUrl && !j.isPaused)
      .map((j) => job("devitjobs", j._id, j.company, j.name,
        `https://devitjobs.uk/jobs/${j.jobUrl}`, {
        location: [j.actualCity || j.cityCategory, "UK"].filter(Boolean).join(", "),
        description: [j.jobType, j.expLevel, (j.technologies || []).join(", ")]
          .filter(Boolean).join(" · "),
        postedAt: iso(j.activeFrom),
        remote: /remote/i.test(j.workplace || "") || /remote/i.test(j.remoteType || ""),
        salary: [j.annualSalaryFrom || null, j.annualSalaryTo || null, "GBP", "year"],
      }));
  },
  async remoteok() {
    const d = await getJSON("https://remoteok.com/api");
    return (Array.isArray(d) ? d : []).filter((j) => j.id && j.position)
      .map((j) => job("remoteok", j.id, j.company, j.position, j.url, {
        location: j.location || "Remote", description: stripHtml(j.description),
        postedAt: iso(j.date), remote: true,
        salary: [j.salary_min || null, j.salary_max || null, "USD", "year"],
      }));
  },
  async jobicy() {
    const d = await getJSON("https://jobicy.com/api/v2/remote-jobs?count=100");
    return (d.jobs || []).map((j) => job("jobicy", j.id, j.companyName, j.jobTitle, j.url, {
      location: j.jobGeo, description: stripHtml(j.jobDescription || j.jobExcerpt),
      postedAt: iso(j.pubDate), remote: true,
      salary: [j.annualSalaryMin || null, j.annualSalaryMax || null,
               symbolFor(j.salaryCurrency || j.annualSalaryCurrency) || "USD", "year"],
    }));
  },
  async himalayas() {
    const d = await getJSON("https://himalayas.app/jobs/api?limit=100");
    return (d.jobs || []).map((j) => job("himalayas", j.guid || j.applicationLink,
      j.companyName, j.title, j.applicationLink, {
      location: (j.locationRestrictions || []).join(", ") || "Worldwide",
      description: stripHtml(j.description || j.excerpt),
      postedAt: iso(j.pubDate || j.publishedDate), remote: true,
      salary: [j.minSalary || null, j.maxSalary || null, symbolFor(j.currency) || "USD", "year"],
    }));
  },
  async workingnomads() {
    const d = await getJSON("https://www.workingnomads.com/api/exposed_jobs/");
    return (Array.isArray(d) ? d : []).map((j) => job("workingnomads",
      (j.url || "").split("/").pop() || j.url, j.company_name, j.title, j.url, {
      location: j.location || "Worldwide", description: stripHtml(j.description),
      postedAt: iso(j.pub_date), remote: true,
    }));
  },
};

/**
 * Τραβάει τα πάντα παράλληλα. Μια πηγή που πέφτει δεν ρίχνει ποτέ το scan.
 * onProgress(label, count, error) για ζωντανή ένδειξη στο UI.
 */
export async function fetchAll(targets = [], boards = [], query = "", onProgress = () => {}, opts = {}) {
  const tasks = [];

  for (const t of targets) {
    const fn = ATS[t.provider];
    if (!fn) continue;
    tasks.push(
      fn(t.slug, t.name)
        .then((r) => { onProgress(t.name, r.length, null); return r; })
        .catch((e) => { onProgress(t.name, 0, String(e.message || e)); return []; })
    );
  }
  for (const b of boards) {
    const fn = BOARDS[b];
    if (!fn) continue;
    tasks.push(
      fn(query, opts)
        .then((r) => { onProgress(b, r.length, null); return r; })
        .catch((e) => { onProgress(b, 0, String(e.message || e)); return []; })
    );
  }

  const results = await Promise.all(tasks);
  const seen = new Set();
  const out = [];
  for (const list of results) {
    for (const j of list) {
      if (!j.url || !j.title || seen.has(j.id)) continue;
      seen.add(j.id);
      out.push(j);
    }
  }
  return out;
}
