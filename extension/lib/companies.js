/*
 * Έτοιμες εταιρείες ανά κλάδο, ώστε ο νέος χρήστης να μη χρειάζεται να ξέρει
 * ποια εταιρεία τρέχει ποιο ATS. Όλες επαληθευμένες ότι απαντούν.
 */
export const LIBRARY = [
  { provider: "greenhouse", slug: "datadog", name: "Datadog", industries: ["tech", "saas"] },
  { provider: "greenhouse", slug: "cloudflare", name: "Cloudflare", industries: ["tech", "saas"] },
  { provider: "greenhouse", slug: "gitlab", name: "GitLab", industries: ["tech", "saas"] },
  { provider: "greenhouse", slug: "elastic", name: "Elastic", industries: ["tech", "saas"] },
  { provider: "greenhouse", slug: "databricks", name: "Databricks", industries: ["tech", "ai", "data"] },
  { provider: "ashby", slug: "snowflake", name: "Snowflake", industries: ["tech", "data"] },
  { provider: "greenhouse", slug: "figma", name: "Figma", industries: ["tech", "design"] },
  { provider: "greenhouse", slug: "reddit", name: "Reddit", industries: ["tech", "media"] },
  { provider: "greenhouse", slug: "discord", name: "Discord", industries: ["tech", "media"] },
  { provider: "greenhouse", slug: "airtable", name: "Airtable", industries: ["tech", "saas"] },
  { provider: "greenhouse", slug: "anthropic", name: "Anthropic", industries: ["tech", "ai"] },
  { provider: "ashby", slug: "openai", name: "OpenAI", industries: ["tech", "ai"] },
  { provider: "greenhouse", slug: "scaleai", name: "Scale AI", industries: ["tech", "ai"] },
  { provider: "greenhouse", slug: "stripe", name: "Stripe", industries: ["tech", "fintech"] },
  { provider: "greenhouse", slug: "remotecom", name: "Remote.com", industries: ["tech", "hr"] },
  { provider: "greenhouse", slug: "robinhood", name: "Robinhood", industries: ["fintech", "trading"] },
  { provider: "greenhouse", slug: "chime", name: "Chime", industries: ["fintech"] },
  { provider: "greenhouse", slug: "affirm", name: "Affirm", industries: ["fintech"] },
  { provider: "greenhouse", slug: "marqeta", name: "Marqeta", industries: ["fintech"] },
  { provider: "greenhouse", slug: "n26", name: "N26", industries: ["fintech", "banking"] },
  { provider: "smartrecruiters", slug: "Wise", name: "Wise", industries: ["fintech", "banking"] },
  { provider: "ashby", slug: "ramp", name: "Ramp", industries: ["fintech", "saas"] },
  { provider: "greenhouse", slug: "coinbase", name: "Coinbase", industries: ["crypto", "fintech", "trading"] },
  { provider: "greenhouse", slug: "bitpanda", name: "Bitpanda", industries: ["crypto", "fintech"] },
  { provider: "greenhouse", slug: "gemini", name: "Gemini", industries: ["crypto", "trading"] },
  { provider: "greenhouse", slug: "fireblocks", name: "Fireblocks", industries: ["crypto", "tech"] },
  { provider: "greenhouse", slug: "bitgo", name: "BitGo", industries: ["crypto"] },
  { provider: "greenhouse", slug: "falconx", name: "FalconX", industries: ["crypto", "trading"] },
  { provider: "greenhouse", slug: "binance", name: "Binance", industries: ["crypto", "trading"] },
  { provider: "lever", slug: "ledger", name: "Ledger", industries: ["crypto"] },
  { provider: "greenhouse", slug: "airbnb", name: "Airbnb", industries: ["consumer", "travel"] },
  { provider: "greenhouse", slug: "instacart", name: "Instacart", industries: ["consumer", "retail"] },
  { provider: "smartrecruiters", slug: "DeliveryHero", name: "Delivery Hero", industries: ["consumer", "logistics"] },
  { provider: "greenhouse", slug: "cabify", name: "Cabify", industries: ["consumer", "mobility"] },
  { provider: "ashby", slug: "nubank", name: "Nubank", industries: ["fintech", "banking"] },
  { provider: "greenhouse", slug: "riotgames", name: "Riot Games", industries: ["gaming"] },
  { provider: "greenhouse", slug: "kaizengaming", name: "Kaizen Gaming", industries: ["gaming", "betting"] },
  { provider: "greenhouse", slug: "coursera", name: "Coursera", industries: ["education"] },
  { provider: "greenhouse", slug: "duolingo", name: "Duolingo", industries: ["education"] },
  { provider: "workable", slug: "epignosis", name: "Epignosis", industries: ["education", "saas"] },
  { provider: "greenhouse", slug: "cerebral", name: "Cerebral", industries: ["health"] },
  { provider: "greenhouse", slug: "flexport", name: "Flexport", industries: ["logistics", "tech"] },
  { provider: "greenhouse", slug: "klaviyo", name: "Klaviyo", industries: ["marketing", "saas"] },
  { provider: "smartrecruiters", slug: "Accor", name: "Accor", industries: ["hospitality", "travel"] },
  { provider: "workable", slug: "skroutz", name: "Skroutz", industries: ["retail", "tech"] },

  // Workday — slug = "tenant/datacenter/site" (φαίνεται στο URL της καριέρας τους)
  { provider: "workday", slug: "nvidia/wd5/NVIDIAExternalCareerSite", name: "NVIDIA", industries: ["tech", "ai"] },
  { provider: "workday", slug: "salesforce/wd12/External_Career_Site", name: "Salesforce", industries: ["tech", "saas"] },
  { provider: "workday", slug: "adobe/wd5/external_experienced", name: "Adobe", industries: ["tech", "design"] },
  { provider: "workday", slug: "sonyglobal/wd1/SonyGlobalCareers", name: "Sony", industries: ["media", "gaming", "consumer"] },
];

export const ALL_INDUSTRIES = [...new Set(LIBRARY.flatMap((c) => c.industries))].sort();

export function pickCompanies(industries = [], limit = 25) {
  const wanted = new Set(industries.map((i) => i.toLowerCase()));
  let chosen = wanted.size
    ? LIBRARY.filter((c) => c.industries.some((i) => wanted.has(i)))
    : LIBRARY;
  if (!chosen.length) chosen = LIBRARY;
  return chosen.slice(0, limit).map(({ provider, slug, name }) => ({ provider, slug, name }));
}

/** Κλάδοι που δεν έχουν εταιρείες εδώ — τους καλύπτουν τα job boards. */
export const uncovered = (industries = []) =>
  industries.filter((i) => !ALL_INDUSTRIES.includes(i.toLowerCase()));
