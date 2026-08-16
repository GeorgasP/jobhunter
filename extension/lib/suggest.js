/*
 * Λεξιλόγιο για τα πεδία «job titles» και «where can you work».
 *
 * Η ουσία: οι προτάσεις δεν βγαίνουν από λίστα που φαντάστηκε κάποιος, αλλά
 * από τις αγγελίες που έχουν ήδη κατέβει. Αν οι εταιρείες γράφουν «Customer
 * Support Specialist», αυτό θα δεις — όχι το «Customer Care» που σκέφτηκες.
 * Δίπλα σε κάθε πρόταση φαίνεται σε πόσες αγγελίες εμφανίζεται.
 */

import { ALL_PROFESSIONS, professionsFor } from "./professions.js";

/* ── Καθάρισμα τίτλου ─────────────────────────────────────── */
const SENIORITY = /^(senior|sr\.?|junior|jr\.?|lead|principal|staff|head of|chief|vp|vice president|intern|trainee|graduate|entry[- ]level|mid[- ]level)\s+/i;
const GENDER = /\((?:[mwfdhx]\s*\/\s*)+[mwfdhx]\)|\s*\(?[mwfdhx]\/[mwfdhx](?:\/[mwfdhx])?\)?\s*$/gi;
const TAIL = /\s*[-–—|@,:]\s*(remote|hybrid|onsite|on-site|full[- ]time|part[- ]time|contract|permanent|freelance|emea|apac|latam|us|uk|eu|europe|germany|spain|greece|poland|india|brazil|canada|australia|singapore|dubai|[a-z]{2,}\s*(city|region))\b.*$/i;
const NOISE = /\b(m\/w\/d|w\/m\/d|f\/m\/d|all genders|remote|hybrid|full[- ]time|part[- ]time|fixed[- ]term|maternity cover|contract)\b/gi;

// Λέξεις που κάνουν ένα κομμάτι να είναι ρόλος και όχι τοποθεσία/παράρτημα.
const ROLEISH = /(manager|engineer|developer|specialist|analyst|consultant|designer|director|officer|assistant|representative|executive|coordinator|architect|scientist|technician|nurse|teacher|chef|driver|accountant|recruiter|agent|advisor|administrator|support|success|sales|marketing|lead|intern|writer|editor|operator|planner|buyer|trainer|therapist|paralegal|controller|auditor)/i;

export function normalizeTitle(raw) {
  let t = (raw || "")
    .replace(/\(.*?\)/g, " ")
    .replace(GENDER, " ")
    .replace(TAIL, "")
    .replace(NOISE, " ")
    .replace(/[–—]/g, "-")
    .replace(/\s+([,:])/g, "$1")
    .replace(/\s*[-|,:/]\s*$/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();

  // «Data Analyst, Berlin» → «Data Analyst». Ό,τι είναι μετά από κόμμα και δεν
  // μοιάζει με ρόλο είναι σχεδόν πάντα πόλη, ομάδα ή τμήμα.
  for (let i = 0; i < 2 && t.includes(","); i++) {
    const cut = t.lastIndexOf(",");
    const tail = t.slice(cut + 1).trim();
    if (tail && tail.split(/\s+/).length <= 3 && !ROLEISH.test(tail)) t = t.slice(0, cut).trim();
    else break;
  }

  let previous;
  do { previous = t; t = t.replace(SENIORITY, ""); } while (t !== previous);

  // Πολύ μεγάλοι τίτλοι είναι περιγραφές, όχι ρόλοι
  if (t.split(/\s+/).length > 6 || t.length < 3) return "";
  return t.replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ── Καθάρισμα τοποθεσίας ─────────────────────────────────── */
const LOC_NOISE = /\b(remote|hybrid|onsite|on-site|work from home|anywhere in|based in|or)\b/gi;

export function splitLocations(raw) {
  if (!raw) return [];
  const out = [];
  for (const piece of raw.split(/[,;/|·•]|\s+-\s+|\bor\b/i)) {
    let p = piece.replace(LOC_NOISE, " ").replace(/[()]/g, " ").replace(/\s{2,}/g, " ").trim();
    if (p.length < 2 || p.length > 40) continue;
    if (/^\d+$/.test(p)) continue;
    out.push(p.replace(/\b\w/g, (c) => c.toUpperCase()));
  }
  if (/remote|anywhere|work from home/i.test(raw)) out.push("Remote");
  if (/worldwide|global/i.test(raw)) out.push("Worldwide");
  return out;
}

/* ── Σπόροι για την πρώτη φορά, πριν κατέβει οτιδήποτε ────── */
export const SEED_LOCATIONS = [
  "Remote", "Worldwide", "Europe", "EU", "EMEA", "APAC", "LATAM", "ANZ",
  "United Kingdom", "Ireland", "Germany", "France", "Spain", "Portugal", "Italy",
  "Netherlands", "Belgium", "Poland", "Greece", "Romania", "Bulgaria", "Czechia",
  "Sweden", "Norway", "Denmark", "Finland", "Switzerland", "Austria", "Cyprus",
  "United States", "Canada", "Mexico", "Brazil", "Argentina", "Colombia", "Chile",
  "India", "Singapore", "Japan", "Australia", "New Zealand", "Philippines", "Indonesia",
  "United Arab Emirates", "Saudi Arabia", "Israel", "Turkey", "Egypt",
  "South Africa", "Nigeria", "Kenya", "Morocco",
  "London", "Berlin", "Paris", "Madrid", "Barcelona", "Amsterdam", "Dublin",
  "Lisbon", "Athens", "Warsaw", "Bucharest", "Milan", "Munich", "Zurich",
  "New York", "San Francisco", "Toronto", "Dubai", "Bangalore", "Sydney",
];

/* ── Χτίσιμο λεξιλογίου από τις κατεβασμένες αγγελίες ─────── */
function tally(values) {
  const counts = new Map();
  for (const v of values) {
    if (!v) continue;
    const key = v.toLowerCase();
    const entry = counts.get(key);
    if (entry) entry.count++;
    else counts.set(key, { label: v, count: 1 });
  }
  return [...counts.values()].sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

export function buildVocabulary(jobs = [], { industries = [] } = {}) {
  const titles = tally(jobs.map((j) => normalizeTitle(j.title)));
  const locations = tally(jobs.flatMap((j) => splitLocations(j.location)));

  // Πρώτα τα επαγγέλματα των κλάδων που διάλεξε ο χρήστης, μετά τα υπόλοιπα:
  // όποιος δήλωσε «υγεία» πρέπει να βλέπει φυσικοθεραπευτή πριν από λογιστή.
  const seeds = [...professionsFor(industries), ...ALL_PROFESSIONS];
  const seen = new Set(titles.map((t) => t.label.toLowerCase()));
  for (const s of seeds) {
    if (seen.has(s.toLowerCase())) continue;
    seen.add(s.toLowerCase());
    titles.push({ label: s, count: 0 });
  }

  const seenLoc = new Set(locations.map((l) => l.label.toLowerCase()));
  for (const s of SEED_LOCATIONS) if (!seenLoc.has(s.toLowerCase())) locations.push({ label: s, count: 0 });

  return { titles, locations };
}

/* ── Αναζήτηση καθώς πληκτρολογείς ────────────────────────── */
const tokens = (s) => s.toLowerCase().split(/[^a-z0-9+]+/i).filter(Boolean);

/**
 * Ανοχή σε τυπογραφικά: «acount manger» πρέπει να βρίσκει «Account Manager».
 * Φραγμένη απόσταση Levenshtein — σταματάει μόλις ξεπεράσει το όριο.
 */
function nearlyEqual(a, b) {
  if (a === b) return true;
  if (a.startsWith(b) || b.startsWith(a)) return true;
  const limit = Math.min(a.length, b.length) <= 5 ? 1 : 2;
  if (Math.abs(a.length - b.length) > limit || Math.min(a.length, b.length) < 4) return false;

  let previous = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const current = [i];
    let best = i;
    for (let j = 1; j <= b.length; j++) {
      current[j] = Math.min(
        previous[j] + 1,
        current[j - 1] + 1,
        previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1),
      );
      best = Math.min(best, current[j]);
    }
    if (best > limit) return false;
    previous = current;
  }
  return previous[b.length] <= limit;
}

/**
 * Ταξινομεί με βάση το πόσο ταιριάζει ΚΑΙ πόσο συχνά εμφανίζεται στις
 * αγγελίες — ώστε το «customer care» να φέρνει πρώτο το «Customer Support
 * Specialist» που όντως υπάρχει σε 200 αγγελίες.
 */
export function search(vocabulary, query, limit = 8) {
  const q = (query || "").trim().toLowerCase();
  if (!q) return vocabulary.slice(0, limit);

  const qt = tokens(q);
  const scored = [];

  for (const entry of vocabulary) {
    const label = entry.label.toLowerCase();
    let score = 0;

    if (label === q) score = 1000;
    else if (label.startsWith(q)) score = 700;
    else if (label.includes(q)) score = 500;
    else {
      const lt = tokens(label);
      let exact = 0, fuzzy = 0;
      for (const t of qt) {
        if (lt.some((l) => l.startsWith(t) || t.startsWith(l))) exact++;
        else if (lt.some((l) => nearlyEqual(l, t))) fuzzy++;
      }
      if (!exact && !fuzzy) continue;
      score = 200 * ((exact + fuzzy * 0.7) / qt.length) - Math.abs(lt.length - qt.length) * 5;
      if (score < 55) continue;
    }

    // Η συχνότητα στις αγγελίες σπάει τις ισοπαλίες
    scored.push({ ...entry, score: score + Math.min(Math.log2(entry.count + 1) * 12, 90) });
  }

  return scored.sort((a, b) => b.score - a.score).slice(0, limit);
}
