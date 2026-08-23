/*
 * Service worker — η «μηχανή» του JobHunter.
 *
 * • Καθημερινό αυτόματο scan (chrome.alarms) με ειδοποίηση για νέα matches
 * • Badge με τον αριθμό των matches
 * • API μηνυμάτων για το UI και για το content script (autofill)
 */
import * as store from "./lib/store.js";
import { fetchAll } from "./lib/sources.js";
import { rankJobs } from "./lib/matcher.js";
import { generateLetter } from "./lib/letters.js";
import { pickCompanies } from "./lib/companies.js";
import { refreshRates } from "./lib/fx.js";
import { initI18n, t } from "./lib/i18n.js";

const ALARM = "jobhunter-daily";
let scanning = false;

/* ── Μεταφορά ρυθμίσεων σε ενημερώσεις ────────────────────────
 * Το αποθηκευμένο profile υπερισχύει των προεπιλογών. Χωρίς αυτό, όποιος
 * έχει ήδη εγκαταστήσει το extension δεν θα έβλεπε ποτέ τις νέες πηγές —
 * θα αναρωτιόταν γιατί οι άλλοι βρίσκουν περισσότερες αγγελίες.
 * Οι πηγές που έχει ξε-τσεκάρει ο ίδιος δεν επιστρέφουν ποτέ.
 */
const MIGRATIONS = [
  { version: 2, boards: ["themuse", "weworkremotely", "landingjobs", "cryptojobs"] },
  { version: 3, boards: ["devitjobs", "adzuna"] },
  { version: 4, boards: ["psf"] },
  { version: 5, boards: ["skywalker"] },
  { version: 6, boards: ["ordino"] },
];
const SCHEMA_VERSION = MIGRATIONS[MIGRATIONS.length - 1].version;

async function migrate() {
  const state = await store.getState();
  const from = state.schemaVersion || 1;
  if (from >= SCHEMA_VERSION) return null;

  const profile = await store.getProfile();
  const boards = [...profile.boards];
  const added = [];
  for (const step of MIGRATIONS) {
    if (step.version <= from) continue;
    for (const b of step.boards || []) {
      if (!boards.includes(b)) { boards.push(b); added.push(b); }
    }
  }
  if (added.length) await store.saveProfile({ boards });
  await store.saveState({ schemaVersion: SCHEMA_VERSION });
  return added;
}

/* Κρατάμε την υπόσχεση, δεν την πετάμε. Ο service worker ξυπνάει τη στιγμή που
   πατάς «Αναζήτηση» — αν η σάρωση διαβάσει το profile πριν προλάβει να γραφτεί
   η μεταφορά, τρέχει με τις παλιές πηγές και δεν βρίσκει τίποτα. Έχει ξανασυμβεί:
   είναι ακριβώς η πρώτη σάρωση μετά από ενημέρωση, δηλαδή η μόνη που κοιτάς. */
const migrated = migrate()
  .then((added) => {
    if (added?.length) console.info(`JobHunter: added new job boards — ${added.join(", ")}`);
  })
  .catch((e) => console.warn("JobHunter: migration failed —", e));

/* ── Lifecycle ────────────────────────────────────────────── */
chrome.runtime.onInstalled.addListener(async (details) => {
  chrome.alarms.create(ALARM, { periodInMinutes: 60 * 12, delayInMinutes: 3 });
  if (details.reason === "install") {
    chrome.tabs.create({ url: chrome.runtime.getURL("onboarding.html") });
  }
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create(ALARM, { periodInMinutes: 60 * 12, delayInMinutes: 3 });
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== ALARM) return;
  const profile = await store.getProfile();
  if (!profile.autoScan || !(await store.isOnboarded())) return;
  await runScan({ silent: true });
});

/* ── Badge ────────────────────────────────────────────────── */
async function refreshBadge() {
  const matches = await currentMatches();
  const n = matches.length;
  await chrome.action.setBadgeText({ text: n ? String(Math.min(n, 999)) : "" });
  await chrome.action.setBadgeBackgroundColor({ color: "#5b8cff" });
  return n;
}

/* ── Matches ──────────────────────────────────────────────── */
async function currentMatches() {
  await migrated;
  await refreshRates();
  const [profile, jobs, apps, state] = await Promise.all([
    store.getProfile(), store.getJobs(), store.getApps(), store.getState(),
  ]);
  return rankJobs(jobs, profile, {
    dismissed: state.dismissed || [],
    appliedIds: apps.map((a) => a.jobId),
  });
}

/* ── Scan ─────────────────────────────────────────────────── */
async function runScan({ silent = false } = {}) {
  if (scanning) return { ok: false, error: t("error.scanRunning") };
  scanning = true;
  const started = Date.now();

  try {
    await migrated;
    const profile = await store.getProfile();
    const targets = profile.targets?.length ? profile.targets : pickCompanies(profile.industries);
    const sources = [];

    const jobs = await fetchAll(targets, profile.boards, "", (label, count, error) => {
      sources.push({ label, count, error });
    }, {
      maxAgeDays: profile.maxAgeDays,
      adzuna: {
        appId: profile.adzunaAppId,
        appKey: profile.adzunaKey,
        countries: profile.adzunaCountries,
      },
    });

    const { added, total } = await store.mergeJobs(jobs);
    const matches = await currentMatches();

    const history = (await store.getState()).history || [];
    history.push({ at: new Date().toISOString(), seen: jobs.length, added, matches: matches.length });

    await store.saveState({
      lastScan: new Date().toISOString(),
      lastSources: sources,
      history: history.slice(-30),
    });

    await refreshBadge();

    if (!silent || added > 0) {
      const profileNow = await store.getProfile();
      await initI18n(profileNow.uiLanguage);
      if (profileNow.notify && matches.length) {
        chrome.notifications.create({
          type: "basic",
          iconUrl: chrome.runtime.getURL("icons/128.png"),
          title: t("notify.title", { n: matches.length }),
          message: added
            ? t("notify.body", { added, company: matches[0].company, title: matches[0].title })
            : t("notify.bodyNoNew", { company: matches[0].company, title: matches[0].title }),
          priority: 1,
        });
      }
    }

    return {
      ok: true, seen: jobs.length, added, total,
      matches: matches.length, sources,
      seconds: Math.round((Date.now() - started) / 1000),
    };
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  } finally {
    scanning = false;
  }
}

/* ── Apply ────────────────────────────────────────────────── */
async function applyToJob(jobId, method = "assisted") {
  const [profile, cv, jobs] = await Promise.all([
    store.getProfile(), store.getCV(), store.getJobs(),
  ]);
  const jobItem = jobs.find((j) => j.id === jobId);
  if (!jobItem) return { ok: false, error: t("error.jobNotFound") };

  let letter = { text: "", model: null };
  if (method !== "manual") letter = await generateLetter(jobItem, profile, cv);

  const app = await store.addApp({
    jobId, company: jobItem.company, title: jobItem.title, url: jobItem.url,
    location: jobItem.location, source: jobItem.source,
    method, status: "prepared", preparedAt: new Date().toISOString(),
    coverLetter: letter.text, letterModel: letter.model,
  });
  if (!app) return { ok: false, error: t("error.alreadyApplied") };

  await refreshBadge();
  return { ok: true, app, letterModel: letter.model, letterError: letter.error || null };
}

/* ── Prefill payload για το content script ────────────────── */
const idsIn = (url) => new Set((url.match(/\d{5,}/g) || []).concat(
  (url.split("?")[0].split("/").filter(Boolean).slice(-1)[0] || "").toLowerCase()
));

async function prefillFor(pageUrl) {
  const [profile, cv, apps] = await Promise.all([
    store.getProfile(), store.getCV(), store.getApps(),
  ]);
  if (!apps.length) {
    return { ok: false, error: t("fill.nothingPrepared") };
  }

  const pageIds = idsIn(pageUrl || "");
  let app = apps.find((a) => a.url === pageUrl);
  if (!app) {
    app = apps.find((a) => {
      const ids = idsIn(a.url || "");
      return [...pageIds].some((k) => k && ids.has(k));
    });
  }
  if (!app) app = apps.find((a) => a.status === "prepared") || apps[0];

  const parts = (profile.name || "").trim().split(/\s+/);
  return {
    ok: true,
    applicationId: app.id,
    job: { company: app.company, title: app.title, url: app.url },
    answers: {
      full_name: profile.name,
      first_name: parts[0] || "",
      last_name: parts.slice(1).join(" "),
      email: profile.email,
      phone: profile.phone,
      location: profile.location,
      linkedin: profile.linkedin,
      github: profile.github,
      website: profile.linkedin || profile.github,
      work_authorization: profile.workAuthorization,
      notice_period: profile.noticePeriod,
      salary_expectation: profile.salaryMin ? String(profile.salaryMin) : "",
      how_did_you_hear: "Company careers page",
    },
    cover_letter: app.coverLetter || "",
    cv: cv ? { filename: cv.filename, mime: cv.mime, base64: cv.base64 } : null,
  };
}

/* ── Message API ──────────────────────────────────────────── */
const HANDLERS = {
  scan: () => runScan({ silent: false }),
  matches: async () => ({ ok: true, matches: (await currentMatches()).slice(0, 200) }),
  apply: (msg) => applyToJob(msg.jobId, msg.method),
  prefill: (msg) => prefillFor(msg.url),
  dismiss: async (msg) => { await store.dismissJob(msg.jobId); await refreshBadge(); return { ok: true }; },
  refreshBadge: async () => ({ ok: true, count: await refreshBadge() }),
  /* Αγγελία που είδε ο χρήστης κάπου χωρίς API και θέλησε να κρατήσει.
     Μπαίνει στην ίδια λίστα με τις υπόλοιπες και βαθμολογείται κανονικά. */
  saveJob: async (msg) => {
    const j = msg.job || {};
    if (!j.title || !j.url) return { ok: false, error: "missing title or url" };
    const id = `saved:${j.url}|${j.title}`.slice(0, 120);
    const { added } = await store.mergeJobs([{
      id, source: "saved",
      company: (j.company || "—").trim(),
      title: j.title.trim(),
      location: (j.location || "").trim(),
      description: [j.description, j.contactEmail && `
${j.contactEmail}`]
        .filter(Boolean).join(""),
      url: j.url,
      postedAt: new Date().toISOString(),
      remote: /remote|εξ αποστάσεως/i.test(`${j.title} ${j.location}`),
      salaryMin: null, salaryMax: null, salaryCurrency: null, salaryPeriod: "year",
      lastSeen: new Date().toISOString(),
    }]);
    await refreshBadge();
    return { ok: true, added };
  },

  markSent: async (msg) => {
    await store.updateApp(msg.applicationId, { status: "sent", sentAt: new Date().toISOString() },
                          "Submitted from the application page");
    return { ok: true };
  },
};

chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  const handler = HANDLERS[msg?.type];
  if (!handler) return false;
  Promise.resolve(handler(msg)).then(respond).catch((e) => respond({ ok: false, error: String(e.message || e) }));
  return true;                                   // async
});
