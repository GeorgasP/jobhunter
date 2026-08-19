/*
 * Αποθήκευση — chrome.storage.local, τίποτα δεν φεύγει από τον υπολογιστή.
 *
 * Κλειδιά:
 *   profile      τι ψάχνει ο χρήστης + στοιχεία επικοινωνίας
 *   cv           { filename, mime, base64, text }
 *   jobs         [] αγγελίες (κρατάμε τις πιο πρόσφατες MAX_JOBS)
 *   apps         [] αιτήσεις με ιστορικό
 *   state        { lastScan, lastCounts, seenIds }
 */

// Ένα scan φέρνει ~2.000 αγγελίες. Αν το όριο είναι κάτω από αυτό, κάθε scan
// πετάει και ξαναγράφει τις ίδιες θέσεις — και όλες μοιάζουν «νέες».
export const MAX_JOBS = 5000;
export const DESC_LIMIT = 2500;

export const DEFAULT_PROFILE = {
  name: "", email: "", phone: "", location: "",
  linkedin: "", github: "", workAuthorization: "", noticePeriod: "Immediately available",
  language: "en",
  uiLanguage: "",
  titles: [],
  locations: ["Remote"],
  blockedLocations: [],
  excludeKeywords: [],
  industries: [],
  salaryMin: null,
  salaryCurrency: "EUR",
  experienceLevel: "mid",
  strictLocation: true,
  remoteOnly: false,
  maxAgeDays: 45,
  minScore: 55,
  boards: ["remotive", "arbeitnow", "remoteok", "jobicy", "himalayas", "workingnomads",
           "themuse", "weworkremotely", "landingjobs", "cryptojobs", "devitjobs", "adzuna", "psf"],
  targets: [],
  autoScan: true,
  notify: true,
  anthropicKey: "",

  // Adzuna: προαιρετικό, δωρεάν κλειδί του ίδιου του χρήστη. Είναι η μόνη πηγή
  // που φέρνει ολόκληρη την αγορά μιας χώρας αντί μόνο για remote τεχνολογία.
  adzunaAppId: "",
  adzunaKey: "",
  adzunaCountries: [],
};

const get = async (keys) => chrome.storage.local.get(keys);
const set = async (obj) => chrome.storage.local.set(obj);

export async function getProfile() {
  const { profile } = await get("profile");
  return { ...DEFAULT_PROFILE, ...(profile || {}) };
}
export async function saveProfile(patch) {
  const profile = { ...(await getProfile()), ...patch };
  await set({ profile });
  return profile;
}
export async function isOnboarded() {
  const p = await getProfile();
  return Boolean(p.titles && p.titles.length);
}

export async function getCV() {
  const { cv } = await get("cv");
  return cv || null;
}
export const saveCV = (cv) => set({ cv });

export async function getJobs() {
  const { jobs } = await get("jobs");
  return jobs || [];
}

/** Προσθέτει νέες αγγελίες χωρίς διπλά· επιστρέφει πόσες ήταν όντως νέες. */
export async function mergeJobs(incoming) {
  const existing = await getJobs();
  const index = new Map(existing.map((j) => [j.id, j]));
  let added = 0;

  for (const job of incoming) {
    if (index.has(job.id)) {
      // Η πηγή είναι η αυθεντία: ανανεώνουμε τα πεδία αντί να κρατάμε ό,τι
      // αποθηκεύτηκε παλιότερα. Έτσι μια διόρθωση στο parsing φτάνει και στις
      // αγγελίες που έχουν ήδη κατέβει.
      const stored = index.get(job.id);
      Object.assign(stored, {
        title: job.title, company: job.company, location: job.location,
        url: job.url, postedAt: job.postedAt || stored.postedAt, remote: job.remote,
        salaryMin: job.salaryMin, salaryMax: job.salaryMax,
        salaryCurrency: job.salaryCurrency, salaryPeriod: job.salaryPeriod,
        lastSeen: job.lastSeen,
      });
      if (job.description) {
        stored.description = job.description.slice(0, DESC_LIMIT);
      }
      continue;
    }
    if (job.description && job.description.length > DESC_LIMIT) {
      job.description = job.description.slice(0, DESC_LIMIT);
    }
    index.set(job.id, job);
    added++;
  }

  const all = [...index.values()]
    .sort((a, b) => (b.postedAt || "").localeCompare(a.postedAt || ""))
    .slice(0, MAX_JOBS);

  await set({ jobs: all });
  return { added, total: all.length };
}

export async function getApps() {
  const { apps } = await get("apps");
  return apps || [];
}
export const saveApps = (apps) => set({ apps });

export async function addApp(app) {
  const apps = await getApps();
  if (apps.some((a) => a.jobId === app.jobId)) return null;
  app.id = Date.now();
  app.events = [{ at: new Date().toISOString(), text: `Prepared (${app.method})` }];
  apps.unshift(app);
  await saveApps(apps);
  return app;
}

export async function updateApp(id, patch, eventText) {
  const apps = await getApps();
  const app = apps.find((a) => a.id === id);
  if (!app) return null;
  Object.assign(app, patch);
  if (eventText) app.events.push({ at: new Date().toISOString(), text: eventText });
  await saveApps(apps);
  return app;
}

export async function getState() {
  const { state } = await get("state");
  return state || { lastScan: null, dismissed: [], history: [] };
}
export async function saveState(patch) {
  const state = { ...(await getState()), ...patch };
  await set({ state });
  return state;
}

export async function dismissJob(jobId) {
  const state = await getState();
  const dismissed = new Set(state.dismissed || []);
  dismissed.add(jobId);
  await saveState({ dismissed: [...dismissed].slice(-3000) });
}
