/* UI του dashboard. Μιλάει με τον service worker μέσω μηνυμάτων. */
import * as store from "./lib/store.js";
import { ALL_INDUSTRIES, pickCompanies } from "./lib/companies.js";
import { readCV, guessFromCV } from "./lib/cv.js";
import { buildVocabulary } from "./lib/suggest.js";
import { createTagField } from "./lib/tagfield.js";
import { refreshRates } from "./lib/fx.js";

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const send = (msg) => chrome.runtime.sendMessage(msg);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function setupCvDragAndDrop() {
  const dropZone = $("#cvbox");
  const fileInput = $("#cv-file");
  if (!dropZone || !fileInput) return;

  let dragDepth = 0;

  dropZone.addEventListener("dragenter", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragDepth++;
    dropZone.classList.add("dragging-file");
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = "copy";
    dropZone.classList.add("dragging-file");
  });

  dropZone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragDepth--;
    if (dragDepth <= 0) {
      dragDepth = 0;
      dropZone.classList.remove("dragging-file");
    }
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragDepth = 0;
    dropZone.classList.remove("dragging-file");

    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    const transfer = new DataTransfer();
    transfer.items.add(file);
    fileInput.files = transfer.files;
    fileInput.dispatchEvent(new Event("change", { bubbles: true }));
  });
}

let profile = null, matches = [], apps = [], state = null, filter = "all";
// Λεξιλόγιο από τις κατεβασμένες αγγελίες — έτσι οι προτάσεις είναι η γραφή
// που χρησιμοποιούν όντως οι εταιρείες.
let vocab = { titles: [], locations: [] };
const fields = {};

const STAGES = [
  { key: "prepared", name: "Prepared", color: "var(--fg-3)" },
  { key: "sent", name: "Sent", color: "var(--accent)" },
  { key: "interview", name: "Interview", color: "var(--warn)" },
  { key: "offer", name: "Offer", color: "var(--ok)" },
  { key: "rejected", name: "Rejected", color: "var(--bad)" },
];

function toast(text, kind = "") {
  $(".toast")?.remove();
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = text;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

const ago = (iso) => {
  if (!iso) return "never";
  const mins = Math.round((Date.now() - Date.parse(iso)) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const h = Math.round(mins / 60);
  return h < 24 ? `${h}h ago` : `${Math.round(h / 24)}d ago`;
};

/* ── Load ─────────────────────────────────────────────────── */
async function load() {
  await refreshRates();
  [profile, apps, state] = await Promise.all([store.getProfile(), store.getApps(), store.getState()]);
  const res = await send({ type: "matches" });
  matches = res?.matches || [];

  const allJobs = await store.getJobs();
  vocab = buildVocabulary(allJobs);

  const initials = (profile.name || "?").split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
  $("#avatar").textContent = initials || "?";
  $("#who-name").textContent = profile.name || "Not set up";
  const jobs = allJobs;
  $("#who-sub").textContent = `${jobs.length} jobs tracked`;
  $("#nav-matches").textContent = matches.length;
  $("#nav-apps").textContent = apps.length;
  $("#sub").textContent = `${matches.length} roles waiting · last scan ${ago(state.lastScan)}`;

  renderStats(jobs.length);
  renderCards();
  renderBoard();
  fillSettings();
}

function renderStats(jobCount) {
  const added = state.history?.at(-1)?.added || 0;
  const sent = apps.filter((a) => a.status !== "prepared").length;
  const interviews = apps.filter((a) => a.status === "interview" || a.status === "offer").length;
  $("#stats").innerHTML = `
    <div class="stat"><div class="k">Jobs tracked</div><div class="v">${jobCount.toLocaleString()}</div>
      <div class="d">${added ? `<em>+${added}</em> in the last scan` : "&nbsp;"}</div></div>
    <div class="stat"><div class="k">Matches</div><div class="v">${matches.length}</div>
      <div class="d">score ≥ ${profile.minScore}</div></div>
    <div class="stat"><div class="k">Applications</div><div class="v">${apps.length}</div>
      <div class="d">${sent} sent · ${apps.length - sent} ready</div></div>
    <div class="stat"><div class="k">Interviews</div><div class="v">${interviews}</div>
      <div class="d">update them in Pipeline</div></div>`;
}

const ringColor = (s) => (s >= 80 ? "var(--ok)" : s >= 65 ? "var(--warn)" : "var(--fg-3)");

function visibleMatches() {
  const today = Date.now() - 36 * 3600 * 1000;
  return matches.filter((m) => {
    if (filter === "remote") return m.remote;
    if (filter === "today") return m.postedAt && Date.parse(m.postedAt) > today;
    if (filter === "salary") return m.salaryMin || m.salaryMax;
    return true;
  });
}

function renderCards() {
  const list = visibleMatches().slice(0, 100);
  $("#count").textContent = `Showing ${list.length} of ${matches.length}`;

  if (!list.length) {
    $("#cards").innerHTML = `<div class="empty"><div class="e">🔍</div>
      <b>${matches.length ? "Nothing under this filter" : "No matches yet"}</b>
      <p>${matches.length ? "Try another filter above."
        : "Hit “Scan now” to search, or widen your job titles and locations in Settings."}</p>
      ${matches.length ? "" : '<button class="btn primary" onclick="document.getElementById(\'scan\').click()">Scan now</button>'}
    </div>`;
    return;
  }

  $("#cards").innerHTML = list.map((m) => `
    <article class="card" data-id="${esc(m.id)}">
      <div class="ring" style="--p:${m.score};--ring:${ringColor(m.score)}"><b>${m.score}</b></div>
      <div>
        <h3><a href="${esc(m.url)}" target="_blank" rel="noopener">${esc(m.title)}</a></h3>
        <div class="meta"><span class="co">${esc(m.company)}</span>
          ${m.location ? `<i class="dot"></i>${esc(m.location)}` : ""}
          <i class="dot"></i><span class="src">${esc(m.source)}</span></div>
        <div class="chips">${(m.chips || []).map((c) => `<span class="chip ${c.kind}">${esc(c.text)}</span>`).join("")}</div>
        <div class="acts">
          <button class="btn primary" data-act="apply">Apply</button>
          <button class="btn" data-act="dismiss">Dismiss</button>
          <a class="btn" href="${esc(m.url)}" target="_blank" rel="noopener">Open posting ↗</a>
        </div>
      </div>
    </article>`).join("");
}

function renderBoard() {
  $("#board").innerHTML = STAGES.map((st) => {
    const items = apps.filter((a) => a.status === st.key);
    return `<div class="col" data-stage="${st.key}">
      <div class="col-h" style="--c:${st.color}"><i></i>${st.name}<span>${items.length}</span></div>
      ${items.length ? items.map((a) => `
        <div class="tile" draggable="true" data-app="${a.id}">
          <b>${esc(a.title)}</b><div class="co">${esc(a.company)}</div>
          <div class="f"><span class="tag">${esc(a.method)}</span>${new Date(a.preparedAt).toLocaleDateString()}</div>
        </div>`).join("") : `<div class="col-empty">nothing here yet</div>`}
    </div>`;
  }).join("");

  let dragged = null;
  $$(".tile").forEach((t) => {
    t.addEventListener("dragstart", () => { dragged = t; t.classList.add("dragging"); });
    t.addEventListener("dragend", () => { dragged = null; t.classList.remove("dragging"); });
    t.addEventListener("click", () => openDrawer(Number(t.dataset.app)));
  });
  $$(".col").forEach((col) => {
    col.addEventListener("dragover", (e) => { e.preventDefault(); col.classList.add("drop"); });
    col.addEventListener("dragleave", () => col.classList.remove("drop"));
    col.addEventListener("drop", async (e) => {
      e.preventDefault();
      col.classList.remove("drop");
      if (!dragged) return;
      const id = Number(dragged.dataset.app);
      const stage = col.dataset.stage;
      await store.updateApp(id, { status: stage }, `Moved to ${stage}`);
      apps = await store.getApps();
      renderBoard();
      renderStats((await store.getJobs()).length);
    });
  });
}

async function openDrawer(id) {
  const app = apps.find((a) => a.id === id);
  if (!app) return;
  $("#drawer-body").innerHTML = `
    <button class="btn" id="close-drawer" style="margin-bottom:16px">← Back</button>
    <h2>${esc(app.title)}</h2>
    <div class="meta">${esc(app.company)}${app.location ? " · " + esc(app.location) : ""} ·
      <a href="${esc(app.url)}" target="_blank" rel="noopener">open posting ↗</a></div>
    <div class="acts" style="margin:18px 0">
      ${STAGES.map((s) => `<button class="btn ${app.status === s.key ? "primary" : ""}" data-stage="${s.key}">${s.name}</button>`).join("")}
    </div>
    ${app.coverLetter ? `<h3 style="font-size:14px;margin-top:18px">Cover letter
       <span style="color:var(--fg-3);font-weight:400">(${esc(app.letterModel || "template")})</span></h3>
       <pre>${esc(app.coverLetter)}</pre>
       <button class="btn" id="copy-letter" style="margin-top:10px">Copy letter</button>` : ""}
    <h3 style="font-size:14px;margin-top:22px">History</h3>
    <ul class="tl">${(app.events || []).map((e) =>
      `<li><span>${new Date(e.at).toLocaleString()}</span>${esc(e.text)}</li>`).join("")}</ul>`;

  $("#drawer").classList.add("on");
  $("#close-drawer").onclick = () => $("#drawer").classList.remove("on");
  $("#copy-letter")?.addEventListener("click", () => {
    navigator.clipboard.writeText(app.coverLetter);
    toast("Cover letter copied", "ok");
  });
  $$("#drawer-body [data-stage]").forEach((b) => b.addEventListener("click", async () => {
    await store.updateApp(id, { status: b.dataset.stage }, `Moved to ${b.dataset.stage}`);
    apps = await store.getApps();
    renderBoard(); openDrawer(id);
  }));
}

$("#drawer").addEventListener("click", (e) => {
  if (e.target.classList.contains("veil")) $("#drawer").classList.remove("on");
});

/* ── Settings ─────────────────────────────────────────────── */
const VOCAB_FOR = {
  titles: () => vocab.titles,
  locations: () => vocab.locations,
  blockedLocations: () => vocab.locations,
  excludeKeywords: () => vocab.titles,
};

const tagValues = (name) => (fields[name] ? fields[name].values : []);

async function fillSettings() {
  for (const key of ["titles", "locations", "blockedLocations", "excludeKeywords"]) {
    const box = document.querySelector(`[data-tags="${key}"]`);
    if (!fields[key]) {
      fields[key] = createTagField(box, { values: profile[key] || [], vocabulary: VOCAB_FOR[key] });
    } else {
      fields[key].values = profile[key] || [];
    }
  }

  ["name", "email", "phone", "location", "linkedin", "workAuthorization",
   "noticePeriod", "language", "experienceLevel", "anthropicKey", "salaryCurrency"]
    .forEach((k) => { if ($("#" + k)) $("#" + k).value = profile[k] ?? ""; });
  $("#salaryMin").value = profile.salaryMin ?? "";
  $("#minScore").value = profile.minScore ?? 55;

  $$("[data-tog]").forEach((t) => t.classList.toggle("on", Boolean(profile[t.dataset.tog])));

  const industryLabels = {
    ai: "AI",
    hr: "HR",
    saas: "SaaS",
    fintech: "Fintech",
  };

  const formatIndustry = (industry) =>
    industryLabels[industry] ??
    industry.charAt(0).toUpperCase() + industry.slice(1);

  $("#industries").innerHTML = ALL_INDUSTRIES.map((i) =>
    `<button class="pick ${profile.industries?.includes(i) ? "on" : ""}" data-i="${i}">${formatIndustry(i)}</button>`).join("");
  $$("#industries .pick").forEach((p) => p.onclick = () => p.classList.toggle("on"));

  const cv = await store.getCV();
  if (cv) {
    $("#cvbox").classList.add("has");
    $("#cv-name").textContent = cv.filename;
    $("#cv-sub").textContent = `${Math.round(cv.size / 1024)} KB · ${cv.text ? cv.text.length.toLocaleString() + " characters read" : "text could not be read"}`;
    $("#cv-pick").textContent = "Replace";
  }
}

$("#cv-pick").onclick = () => $("#cv-file").click();
$("#cv-file").onchange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const cv = await readCV(file);
    await store.saveCV(cv);
    const guess = guessFromCV(cv.text);
    const patch = {};
    for (const k of ["name", "email", "phone", "linkedin", "github"]) {
      if (guess[k] && !$("#" + k)?.value) patch[k] = guess[k];
    }
    if (Object.keys(patch).length) {
      profile = await store.saveProfile(patch);
      toast(`CV saved. Filled in ${Object.keys(patch).join(", ")} from it.`, "ok");
    } else {
      toast(cv.text ? "CV saved and read." : "CV saved (text could not be extracted — a template letter will be used).",
            cv.text ? "ok" : "");
    }
    await load();
  } catch (err) {
    toast("Could not read that file: " + err.message, "bad");
  }
};

$("#save").onclick = async () => {
  const industries = $$("#industries .pick.on").map((p) => p.dataset.i);
  const patch = {
    titles: tagValues("titles"),
    locations: tagValues("locations"),
    blockedLocations: tagValues("blockedLocations"),
    excludeKeywords: tagValues("excludeKeywords"),
    industries,
    targets: pickCompanies(industries),
    salaryMin: parseInt($("#salaryMin").value, 10) || null,
    minScore: parseInt($("#minScore").value, 10) || 55,
  };
  ["name", "email", "phone", "location", "linkedin", "workAuthorization",
   "noticePeriod", "language", "experienceLevel", "anthropicKey", "salaryCurrency"]
    .forEach((k) => { patch[k] = $("#" + k).value.trim(); });
  $$("[data-tog]").forEach((t) => { patch[t.dataset.tog] = t.classList.contains("on"); });

  profile = await store.saveProfile(patch);
  await send({ type: "refreshBadge" });
  await load();
  toast("Saved. Matches re-scored with your new filters.", "ok");
};

$$("[data-tog]").forEach((t) => t.onclick = () => t.classList.toggle("on"));

/* ── Actions ──────────────────────────────────────────────── */
$("#cards").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-act]");
  if (!btn) return;
  const id = btn.closest(".card").dataset.id;

  if (btn.dataset.act === "dismiss") {
    await send({ type: "dismiss", jobId: id });
    matches = matches.filter((m) => m.id !== id);
    renderCards();
    return;
  }

  btn.disabled = true;
  btn.textContent = "Preparing…";
  const res = await send({ type: "apply", jobId: id, method: "assisted" });
  if (!res?.ok) { toast(res?.error || "Something went wrong", "bad"); btn.disabled = false; btn.textContent = "Apply"; return; }

  const job = matches.find((m) => m.id === id);
  window.open(job.url, "_blank", "noopener");
  toast(`Ready. On the form, click “Fill with JobHunter”${res.letterModel === "template" ? "" : " — letter written by Claude"}.`, "ok");
  await load();
});

$$(".chip-filter").forEach((c) => c.onclick = () => {
  $$(".chip-filter").forEach((x) => x.classList.remove("on"));
  c.classList.add("on");
  filter = c.dataset.f;
  renderCards();
});

$("#scan").onclick = async () => {
  const btn = $("#scan");
  btn.disabled = true;
  btn.textContent = "Scanning…";
  const res = await send({ type: "scan" });
  btn.disabled = false;
  btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 3v6h-6"/></svg> Scan now`;
  if (!res?.ok) return toast(res?.error || "Scan failed", "bad");
  const failed = (res.sources || []).filter((s) => s.error).length;
  toast(`Found ${res.seen} postings (${res.added} new) in ${res.seconds}s. ${res.matches} match you.` +
        (failed ? ` ${failed} sources were unreachable.` : ""), "ok");
  await load();
};

const TITLES = {
  matches: ["Matches", () => `${matches.length} roles waiting · last scan ${ago(state.lastScan)}`],
  pipeline: ["Pipeline", () => `${apps.length} applications · drag a card to change its stage`],
  settings: ["Settings", () => "You decide what counts as a match"],
};

$$(".nav-item").forEach((a) => a.onclick = () => {
  $$(".nav-item").forEach((x) => x.classList.remove("on"));
  a.classList.add("on");
  $$(".view").forEach((v) => v.classList.remove("on"));
  $("#v-" + a.dataset.v).classList.add("on");
  $("#ttl").textContent = TITLES[a.dataset.v][0];
  $("#sub").textContent = TITLES[a.dataset.v][1]();
  scrollTo({ top: 0, behavior: "smooth" });
});

$("#theme").onclick = async () => {
  const root = document.documentElement;
  root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
  await chrome.storage.local.set({ theme: root.dataset.theme });
};

chrome.storage.local.get("theme").then(({ theme }) => {
  if (theme) document.documentElement.dataset.theme = theme;
});

store.isOnboarded().then((ok) => {
  if (!ok) location.href = "onboarding.html";
  else {
    setupCvDragAndDrop();
    load();
  }
});