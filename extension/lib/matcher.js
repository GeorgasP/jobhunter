/*
 * Βαθμολογία 0-100: πόσο ταιριάζει μια αγγελία στον χρήστη.
 * Ο τίτλος μετράει πιο πολύ απ' όλα — εκεί κρύβονται τα false positives.
 * Κάθε απόρριψη επιστρέφει λόγο, ώστε το UI να μη μοιάζει μαύρο κουτί.
 */

import { annualIn } from "./fx.js";

const W = { title: 40, location: 25, industry: 10, language: 10, fresh: 10, salary: 5 };

const SENIOR = ["senior", "sr.", "lead", "principal", "staff", "head of", "director",
                "vp ", "vice president", "chief"];
const ENTRY = ["junior", "jr.", "entry", "graduate", "trainee", "intern", "apprentice"];

const GLOBAL_WORDS = ["worldwide", "anywhere", "global", "fully remote"];
const REMOTE_WORDS = ["remote", "anywhere", "worldwide", "work from home", "distributed"];

const REGION_ALIASES = {
  eu: ["eu", "europe", "european", "emea"],
  europe: ["europe", "european", "eu", "emea"],
  emea: ["emea", "europe", "middle east", "africa"],
  us: ["us", "usa", "u.s.", "united states", "america"],
  usa: ["usa", "us", "u.s.", "united states"],
  uk: ["uk", "united kingdom", "england", "britain", "london"],
  uae: ["uae", "united arab emirates", "dubai", "abu dhabi"],
  apac: ["apac", "asia", "asia-pacific", "asia pacific"],
  latam: ["latam", "latin america", "south america"],
  anz: ["anz", "australia", "new zealand"],
};

const LANGUAGE_SIGNALS = {
  el: ["greek", "ελλην", "greece", "athens"],
  es: ["spanish", "español", "espanol", "spain", "madrid", "barcelona"],
  de: ["german", "deutsch", "germany", "berlin", "munich"],
  fr: ["french", "français", "francais", "france", "paris"],
  it: ["italian", "italiano", "italy", "milan", "rome"],
  pt: ["portuguese", "português", "portugal", "brazil", "lisbon"],
  nl: ["dutch", "nederlands", "netherlands", "amsterdam"],
  pl: ["polish", "polska", "poland", "warsaw"],
  ar: ["arabic", "العربية", "dubai", "riyadh"],
  hi: ["hindi", "india", "bangalore", "mumbai"],
};

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const phraseIn = (phrase, text) =>
  new RegExp(`(?<!\\w)${esc(phrase.toLowerCase())}(?!\\w)`).test(text);

const SYMBOLS = { EUR: "€", USD: "$", GBP: "£", PLN: "zł", CHF: "CHF ",
  SEK: "kr", NOK: "kr", DKK: "kr", INR: "₹", JPY: "¥", CAD: "CA$", AUD: "A$",
  BRL: "R$", TRY: "₺", ILS: "₪", CZK: "Kč ", HUF: "Ft ", RON: "lei ",
  AED: "AED ", SGD: "S$", ZAR: "R", MXN: "MX$" };

/**
 * Ο μισθός όπως τον γράφει η αγγελία — δικό της νόμισμα, δική της περίοδος.
 * Καμία μετατροπή: «€45k–60k» στη Γερμανία, «$120k» στις ΗΠΑ, «₹18,00,000»
 * στην Ινδία. Η μετατροπή θα απαιτούσε ισοτιμίες και θα έκρυβε την αλήθεια.
 */
export function formatSalary(jobItem) {
  const min = jobItem.salaryMin, max = jobItem.salaryMax;
  if (!min && !max) return "";

  const currency = SYMBOLS[jobItem.salaryCurrency] ||
    (jobItem.salaryCurrency ? jobItem.salaryCurrency + " " : "");
  const yearly = !jobItem.salaryPeriod || jobItem.salaryPeriod === "year";
  const period = yearly ? "" : ` / ${jobItem.salaryPeriod}`;
  // «55k» βγάζει νόημα για ετήσιο μισθό· για μηνιαίο ή ωρομίσθιο ο κόσμος
  // θέλει το ακριβές ποσό.
  const num = (n) => (yearly && n >= 10000
    ? `${Math.round(n / 1000)}k`
    : n.toLocaleString("en-US"));

  const core = min && max ? `${num(min)}–${num(max)}`
    : min ? `${num(min)}+`
    : `up to ${num(max)}`;

  return `${currency}${core}${period}`;
}

function ageDays(postedAt) {
  if (!postedAt) return null;
  const t = Date.parse(postedAt);
  return isNaN(t) ? null : (Date.now() - t) / 86400000;
}

function locationHits(location, wanted) {
  const hits = [];
  for (const loc of wanted) {
    const low = loc.trim().toLowerCase();
    if (!low) continue;
    if (REMOTE_WORDS.includes(low)) {
      if (REMOTE_WORDS.some((w) => location.includes(w))) hits.push("Remote");
      continue;
    }
    const variants = REGION_ALIASES[low] || [low];
    if (variants.some((v) => location.includes(v))) hits.push(loc);
  }
  return hits;
}

export function scoreJob(jobItem, p) {
  const title = (jobItem.title || "").toLowerCase();
  const location = (jobItem.location || "").toLowerCase();
  const description = (jobItem.description || "").toLowerCase().slice(0, 6000);
  const hay = `${title} ${location} ${description}`;
  const reasons = { chips: [] };

  for (const kw of p.excludeKeywords || []) {
    if (phraseIn(kw, title) || phraseIn(kw, description.slice(0, 1500))) {
      return { score: 0, rejected: `excluded keyword: ${kw}`, reasons };
    }
  }
  if (p.remoteOnly && !(jobItem.remote || hay.includes("remote"))) {
    return { score: 0, rejected: "not remote", reasons };
  }

  const geo = locationHits(location, p.locations || []);
  const globallyOpen = !location || GLOBAL_WORDS.some((w) => location.includes(w));

  const blocked = (p.blockedLocations || []).find((b) => location.includes(b.toLowerCase()));
  if (blocked && !geo.length) return { score: 0, rejected: `blocked location: ${blocked}`, reasons };
  if (p.strictLocation && (p.locations || []).length && !geo.length && !globallyOpen) {
    return { score: 0, rejected: `outside your locations: ${jobItem.location}`, reasons };
  }

  const age = ageDays(jobItem.postedAt);
  if (age != null && p.maxAgeDays && age > p.maxAgeDays) {
    return { score: 0, rejected: `posted ${Math.round(age)} days ago`, reasons };
  }

  let score = 0;

  const titleHits = (p.titles || []).filter((t) => phraseIn(t, title));
  const descHits = (p.titles || []).filter((t) => !titleHits.includes(t) && phraseIn(t, description));
  if (titleHits.length) {
    score += W.title;
    reasons.chips.push({ kind: "good", text: titleHits[0] });
  } else if (descHits.length) {
    score += W.title * 0.35;
    reasons.chips.push({ kind: "", text: `${descHits[0]} (in text)` });
  }

  if (geo.length) {
    score += W.location;
    reasons.chips.push({ kind: "", text: [...new Set(geo)].slice(0, 2).join(" · ") });
  } else if (globallyOpen || !(p.locations || []).length) {
    score += W.location * 0.7;
    reasons.chips.push({ kind: "", text: "Worldwide" });
  }

  const industryHits = (p.industries || []).filter((i) => phraseIn(i, hay));
  if (industryHits.length) {
    score += W.industry;
    reasons.chips.push({ kind: "", text: industryHits[0] });
  }

  const langHits = [];
  for (const lang of p.languages || []) {
    if ((LANGUAGE_SIGNALS[lang] || []).some((m) => hay.includes(m))) langHits.push(lang);
  }
  if (langHits.length) {
    score += W.language;
    reasons.chips.push({ kind: "good", text: `${langHits[0]} speaker` });
  }

  if (age == null) {
    score += W.fresh * 0.5;
  } else {
    const window = Math.max(p.maxAgeDays || 45, 1);
    score += W.fresh * Math.max(0, 1 - age / window);
    const label = age < 1 ? "today" : `${Math.round(age)}d ago`;
    reasons.chips.push({ kind: age > 21 ? "warn" : "", text: label });
  }

  // Ο μισθός δείχνεται ΠΑΝΤΑ όπως τον γράφει η αγγελία. Η σύγκριση με το όριό
  // σου γίνεται αφού ετησιοποιηθεί και μετατραπεί στο δικό σου νόμισμα —
  // αλλιώς «zł12.000/μήνα» θα φαινόταν μεγαλύτερο από «€30.000/έτος».
  const salaryLabel = formatSalary(jobItem);
  if (salaryLabel) {
    if (!p.salaryMin) {
      reasons.chips.push({ kind: "", text: salaryLabel });
    } else {
      const mine = p.salaryCurrency || "EUR";
      const best = annualIn(jobItem.salaryMax || jobItem.salaryMin,
                            jobItem.salaryCurrency, jobItem.salaryPeriod, mine);
      const converted = jobItem.salaryCurrency !== mine || jobItem.salaryPeriod !== "year";

      if (best >= p.salaryMin) {
        score += W.salary;
        reasons.chips.push({ kind: "good", text: salaryLabel });
      } else {
        score -= W.salary * 2;
        // Δείξε και το ισοδύναμο, αλλιώς το «below your minimum» δεν βγάζει
        // νόημα δίπλα σε νούμερο άλλου νομίσματος.
        const hint = converted
          ? ` (≈${SYMBOLS[mine] || mine + " "}${Math.round(best / 1000)}k/yr)` : "";
        reasons.chips.push({ kind: "warn", text: `${salaryLabel} · below your minimum${hint}` });
      }
    }
  }

  const isSenior = SENIOR.some((m) => title.includes(m));
  const isEntry = ENTRY.some((m) => title.includes(m));
  if (p.experienceLevel === "entry" && isSenior) {
    score -= 25; reasons.chips.push({ kind: "warn", text: "senior role" });
  } else if (p.experienceLevel === "senior" && isEntry) {
    score -= 20; reasons.chips.push({ kind: "warn", text: "entry-level role" });
  } else if (p.experienceLevel === "mid" &&
             ["director", "vp ", "chief", "head of"].some((m) => title.includes(m))) {
    score -= 15; reasons.chips.push({ kind: "warn", text: "leadership role" });
  }

  return { score: Math.max(0, Math.min(100, Math.round(score))), rejected: null, reasons };
}

/** Η ίδια θέση ανεβαίνει συχνά σε πολλά boards — κρατάμε μία φορά την καθεμία. */
const dedupeKey = (j) =>
  `${(j.company || "").toLowerCase().replace(/[^a-z0-9]/g, "")}|` +
  `${(j.title || "").toLowerCase().replace(/\(.*?\)/g, "").replace(/[^a-z0-9]/g, "")}`;

/** Βαθμολογεί όλα τα jobs και επιστρέφει ταξινομημένα τα matches. */
export function rankJobs(jobs, profile, { dismissed = [], appliedIds = [] } = {}) {
  const skip = new Set([...dismissed, ...appliedIds]);
  const out = [];
  for (const j of jobs) {
    if (skip.has(j.id)) continue;
    const { score, rejected, reasons } = scoreJob(j, profile);
    if (rejected || score < (profile.minScore || 55)) continue;
    out.push({ ...j, score, chips: reasons.chips });
  }

  out.sort((a, b) => b.score - a.score || (b.postedAt || "").localeCompare(a.postedAt || ""));

  const seen = new Map();
  for (const j of out) {
    const key = dedupeKey(j);
    if (!seen.has(key)) seen.set(key, j);        // ταξινομημένο ήδη: μένει το καλύτερο
  }
  return [...seen.values()];
}
