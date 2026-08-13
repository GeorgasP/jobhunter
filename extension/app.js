/* UI του dashboard. Μιλάει με τον service worker μέσω μηνυμάτων. */
import * as store from "./lib/store.js";
import { ALL_INDUSTRIES, pickCompanies } from "./lib/companies.js";
import { readCV, guessFromCV } from "./lib/cv.js";
import { buildVocabulary } from "./lib/suggest.js";
import { createTagField } from "./lib/tagfield.js";
import { refreshRates } from "./lib/fx.js";
import { initI18n, loadLanguage, applyTranslations, t, LANGUAGES, currentLanguage } from "./lib/i18n.js";

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const send = (msg) => chrome.runtime.sendMessage(msg);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let profile = null, matches = [], apps = [], state = null, filter = "all";
// Λεξιλόγιο από τις κατεβασμένες αγγελίες — έτσι οι προτάσεις είναι η γραφή
// που χρησιμοποιούν όντως οι εταιρείες.
let vocab = { titles: [], locations: [] };
const fields = {};

const STAGES = [
  { key: "prepared", color: "var(--fg-3)" },
  { key: "sent", color: "var(--accent)" },
  { key: "interview", color: "var(--warn)" },
  { key: "offer", color: "var(--ok)" },
  { key: "rejected", color: "var(--bad)" },
];
const stageName = (key) => t(`stage.${key}`);

function toast(text, kind = "") {
  $(".toast")?.remove();
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = text;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

const ago = (iso) => {
  if (!iso) return t("time.never");
  const mins = Math.round((Date.now() - Date.parse(iso)) / 60000);
  if (mins < 1) return t("time.justNow");
  if (mins < 60) return t("time.minutesAgo", { n: mins });
  const h = Math.round(mins / 60);
  return h < 24 ? t("time.hoursAgo", { n: h }) : t("time.daysAgo", { n: Math.round(h / 24) });
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
  $("#who-name").textContent = profile.name || t("nav.notSetUp");
  const jobs = allJobs;
  $("#who-sub").textContent = t("nav.jobsTracked", { count: jobs.length });
  $("#nav-matches").textContent = matches.length;
  $("#nav-apps").textContent = apps.length;
  $("#sub").textContent = t("header.matches.sub", { count: matches.length, when: ago(state.lastScan) });

  renderStats(jobs.length);
  renderCards();
  renderBoard();
  fillSettings();
}

function renderStats(jobCount) {
  const added = state.history?.at(-1)?.added || 0;
  const sent = apps.filter((a) => a.status !== "prepared").length;
  const interviews = apps.filter((a) => a.status === "interview" || a.status === "offer").length;
  // Το νούμερο πρέπει να είναι πράσινο, αλλά η σειρά των λέξεων αλλάζει ανά
  // γλώσσα — γι' αυτό γίνεται escape πρώτα και μπαίνει το HTML μετά.
  const newLine = added
    ? esc(t("stats.newInScan", { n: "%N%" })).replace("%N%", `<em>+${added}</em>`)
    : "&nbsp;";
  $("#stats").innerHTML = `
    <div class="stat"><div class="k">${esc(t("stats.jobsTracked"))}</div><div class="v">${jobCount.toLocaleString()}</div>
      <div class="d">${newLine}</div></div>
    <div class="stat"><div class="k">${esc(t("stats.matches"))}</div><div class="v">${matches.length}</div>
      <div class="d">${esc(t("stats.minScore", { n: profile.minScore }))}</div></div>
    <div class="stat"><div class="k">${esc(t("stats.applications"))}</div><div class="v">${apps.length}</div>
      <div class="d">${esc(t("stats.sentReady", { sent, ready: apps.length - sent }))}</div></div>
    <div class="stat"><div class="k">${esc(t("stats.interviews"))}</div><div class="v">${interviews}</div>
      <div class="d">${esc(t("stats.updateInPipeline"))}</div></div>`;
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
  $("#count").textContent = t("filter.showing", { shown: list.length, total: matches.length });

  if (!list.length) {
    $("#cards").innerHTML = `<div class="empty"><div class="e">🔍</div>
      <b>${esc(t(matches.length ? "cards.empty.noFilter" : "cards.empty.noMatches"))}</b>
      <p>${esc(t(matches.length ? "cards.empty.tryFilter" : "cards.empty.hint"))}</p>
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
          <button class="btn primary" data-act="apply">${esc(t("cards.apply"))}</button>
          <button class="btn" data-act="dismiss">${esc(t("cards.dismiss"))}</button>
          <a class="btn" href="${esc(m.url)}" target="_blank" rel="noopener">${esc(t("cards.open"))}</a>
        </div>
      </div>
    </article>`).join("");
}

function renderBoard() {
  $("#board").innerHTML = STAGES.map((st) => {
    const items = apps.filter((a) => a.status === st.key);
    return `<div class="col" data-stage="${st.key}">
      <div class="col-h" style="--c:${st.color}"><i></i>${esc(stageName(st.key))}<span>${items.length}</span></div>
      ${items.length ? items.map((a) => `
        <div class="tile" draggable="true" data-app="${a.id}">
          <b>${esc(a.title)}</b><div class="co">${esc(a.company)}</div>
          <div class="f"><span class="tag">${esc(a.method)}</span>${new Date(a.preparedAt).toLocaleDateString()}</div>
        </div>`).join("") : `<div class="col-empty">${esc(t("board.empty"))}</div>`}
    </div>`;
  }).join("");

  let dragged = null;
  $$(".tile").forEach((tile) => {
    tile.addEventListener("dragstart", () => { dragged = tile; tile.classList.add("dragging"); });
    tile.addEventListener("dragend", () => { dragged = null; tile.classList.remove("dragging"); });
    tile.addEventListener("click", () => openDrawer(Number(tile.dataset.app)));
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
      await store.updateApp(id, { status: stage }, t("drawer.movedTo", { stage: stageName(stage) }));
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
    <button class="btn" id="close-drawer" style="margin-bottom:16px">${esc(t("drawer.back"))}</button>
    <h2>${esc(app.title)}</h2>
    <div class="meta">${esc(app.company)}${app.location ? " · " + esc(app.location) : ""} ·
      <a href="${esc(app.url)}" target="_blank" rel="noopener">${esc(t("drawer.viewPosting"))}</a></div>
    <div class="acts" style="margin:18px 0">
      ${STAGES.map((s) => `<button class="btn ${app.status === s.key ? "primary" : ""}" data-stage="${s.key}">${esc(stageName(s.key))}</button>`).join("")}
    </div>
    ${app.coverLetter ? `<h3 style="font-size:14px;margin-top:18px">${esc(t("drawer.coverLetter"))}
       <span style="color:var(--fg-3);font-weight:400">(${esc(app.letterModel || "template")})</span></h3>
       <pre>${esc(app.coverLetter)}</pre>
       <button class="btn" id="copy-letter" style="margin-top:10px">${esc(t("drawer.copyLetter"))}</button>` : ""}
    <h3 style="font-size:14px;margin-top:22px">${esc(t("drawer.history"))}</h3>
    <ul class="tl">${(app.events || []).map((e) =>
      `<li><span>${new Date(e.at).toLocaleString()}</span>${esc(e.text)}</li>`).join("")}</ul>`;

  $("#drawer").classList.add("on");
  $("#close-drawer").onclick = () => $("#drawer").classList.remove("on");
  $("#copy-letter")?.addEventListener("click", () => {
    navigator.clipboard.writeText(app.coverLetter);
    toast(t("drawer.letterCopied"), "ok");
  });
  $$("#drawer-body [data-stage]").forEach((b) => b.addEventListener("click", async () => {
    await store.updateApp(id, { status: b.dataset.stage }, t("drawer.movedTo", { stage: stageName(b.dataset.stage) }));
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

  $$("[data-tog]").forEach((el) => el.classList.toggle("on", Boolean(profile[el.dataset.tog])));

  $("#industries").innerHTML = ALL_INDUSTRIES.map((i) =>
    `<button class="pick ${profile.industries?.includes(i) ? "on" : ""}" data-i="${i}">${i}</button>`).join("");
  $$("#industries .pick").forEach((p) => p.onclick = () => p.classList.toggle("on"));

  fillLanguageSelect(currentLanguage());

  const cv = await store.getCV();
  if (cv) {
    $("#cvbox").classList.add("has");
    $("#cv-name").textContent = cv.filename;
    $("#cv-sub").textContent = cv.text
      ? t("settings.cv.read", { kb: Math.round(cv.size / 1024), chars: cv.text.length.toLocaleString() })
      : t("settings.cv.unreadable", { kb: Math.round(cv.size / 1024) });
    $("#cv-pick").textContent = t("settings.cv.replace");
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
      toast(t("toast.cvFilled", { fields: Object.keys(patch).join(", ") }), "ok");
    } else {
      toast(t(cv.text ? "toast.cvSaved" : "toast.cvSavedNoText"), cv.text ? "ok" : "");
    }
    await load();
  } catch (err) {
    toast(t("toast.cvFailed", { error: err.message }), "bad");
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
  $$("[data-tog]").forEach((el) => { patch[el.dataset.tog] = el.classList.contains("on"); });

  profile = await store.saveProfile(patch);
  await send({ type: "refreshBadge" });
  await load();
  toast(t("settings.saved"), "ok");
};

$$("[data-tog]").forEach((el) => el.onclick = () => el.classList.toggle("on"));

/* Ο Chrome δεν φορτώνει ποτέ κώδικα από το internet — τα αρχεία διαβάζονται
   από τον δίσκο. Οπότε: git pull, και μετά αυτό το κουμπί. */
$("#reload-ext").onclick = () => {
  toast(t("settings.update.reloading"));
  setTimeout(() => chrome.runtime.reload(), 400);
};

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
  btn.textContent = t("toast.preparing");
  const res = await send({ type: "apply", jobId: id, method: "assisted" });
  if (!res?.ok) { toast(res?.error || t("toast.somethingWrong"), "bad"); btn.disabled = false; btn.textContent = t("cards.apply"); return; }

  const job = matches.find((m) => m.id === id);
  window.open(job.url, "_blank", "noopener");
  toast(t(res.letterModel === "template" ? "toast.applyReady" : "toast.applyReadyAI"), "ok");
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
  btn.textContent = t("header.scanning");
  const res = await send({ type: "scan" });
  btn.disabled = false;
  btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 3v6h-6"/></svg> Scan now`;
  if (!res?.ok) return toast(res?.error || t("toast.scanFailed"), "bad");
  const failed = (res.sources || []).filter((s) => s.error).length;
  toast(t("toast.scanDone", { seen: res.seen, added: res.added, seconds: res.seconds, matches: res.matches })
        + (failed ? t("toast.scanSourcesFailed", { n: failed }) : ""), "ok");
  await load();
};

const TITLES = {
  matches: () => [t("nav.matches"), t("header.matches.sub", { count: matches.length, when: ago(state.lastScan) })],
  pipeline: () => [t("nav.pipeline"), t("header.pipeline.sub", { count: apps.length })],
  settings: () => [t("nav.settings"), t("header.settings.sub")],
};
$$(".nav-item").forEach((a) => a.onclick = () => {
  $$(".nav-item").forEach((x) => x.classList.remove("on"));
  a.classList.add("on");
  $$(".view").forEach((v) => v.classList.remove("on"));
  $("#v-" + a.dataset.v).classList.add("on");
  const [title, sub] = TITLES[a.dataset.v]();
  $("#ttl").textContent = title;
  $("#sub").textContent = sub;
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

/* ── Γλώσσα διεπαφής ──────────────────────────────────────── */
function fillLanguageSelect(active) {
  const select = $("#uiLanguage");
  if (!select) return;
  select.innerHTML = LANGUAGES.map((l) =>
    `<option value="${l.code}" ${l.code === active ? "selected" : ""}>${esc(l.name)}</option>`).join("");
  select.onchange = async () => {
    await loadLanguage(select.value);
    await store.saveProfile({ uiLanguage: select.value });
    applyTranslations();
    await load();
  };
}

store.getProfile().then(async (p) => {
  const active = await initI18n(p.uiLanguage);
  if (!p.uiLanguage) await store.saveProfile({ uiLanguage: active });
  fillLanguageSelect(active);
  if (!(await store.isOnboarded())) location.href = "onboarding.html";
  else load();
});
