import * as store from "./lib/store.js";
import { readCV, guessFromCV } from "./lib/cv.js";
import { ALL_INDUSTRIES, pickCompanies } from "./lib/companies.js";
import { buildVocabulary } from "./lib/suggest.js";
import { createTagField } from "./lib/tagfield.js";

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let guess = { titles: [] };

function step(n) {
  $$(".step").forEach((s, i) => s.classList.toggle("on", i === n - 1));
  $$(".bar i").forEach((b, i) => b.classList.toggle("on", i < Math.min(n, 3)));
  scrollTo({ top: 0, behavior: "smooth" });
}

/* ── Tag inputs με προτάσεις ──────────────────────────────── */
// Στο onboarding δεν έχει κατέβει τίποτα ακόμα, οπότε το λεξιλόγιο είναι οι
// σπόροι· μετά το πρώτο scan οι προτάσεις βγαίνουν από αληθινές αγγελίες.
let vocab = buildVocabulary([]);
store.getJobs().then((jobs) => { if (jobs.length) vocab = buildVocabulary(jobs); });

const fields = {
  titles: createTagField(document.querySelector('[data-tags="titles"]'),
                         { values: [], vocabulary: () => vocab.titles }),
  locations: createTagField(document.querySelector('[data-tags="locations"]'),
                            { values: ["Remote"], vocabulary: () => vocab.locations }),
};
const tagValues = (n) => fields[n].values;

/* ── Step 1: CV ───────────────────────────────────────────── */
const drop = $("#drop");
drop.onclick = () => $("#file").click();
["dragenter", "dragover"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => handleFile(e.dataTransfer.files[0]));
$("#file").onchange = (e) => handleFile(e.target.files[0]);

async function handleFile(file) {
  if (!file) return;
  drop.innerHTML = `<div class="ic">⏳</div><b>Reading ${esc(file.name)}…</b><span>one moment</span>`;
  try {
    const cv = await readCV(file);
    await store.saveCV(cv);
    guess = guessFromCV(cv.text);

    drop.innerHTML = `<div class="ic">✅</div><b>${esc(cv.filename)}</b>
      <span>${Math.round(cv.size / 1024)} KB${cv.text ? ` · ${cv.text.length.toLocaleString()} characters read` : " · text could not be read"}</span>`;

    const rows = [
      ["Name", guess.name], ["Email", guess.email], ["Phone", guess.phone],
      ["LinkedIn", guess.linkedin],
    ].filter(([, v]) => v);

    $("#found").innerHTML = rows.length
      ? `<div class="found"><div style="font-size:12px;color:var(--fg-3);text-transform:uppercase;
           letter-spacing:.7px;font-weight:600;margin-bottom:8px">Read from your CV</div>
         ${rows.map(([k, v]) => `<div class="row"><span>${k}</span><b>${esc(v)}</b></div>`).join("")}</div>`
      : `<div class="found"><div class="row"><span>No contact details found — you can add them later in Settings.</span></div></div>`;

    await store.saveProfile({
      name: guess.name || "", email: guess.email || "", phone: guess.phone || "",
      linkedin: guess.linkedin || "", github: guess.github || "",
    });
    $("#next1").disabled = false;
  } catch (err) {
    drop.innerHTML = `<div class="ic">⚠️</div><b>Could not read that file</b><span>${esc(err.message)}</span>`;
  }
}

$("#next1").onclick = () => { showSuggestions(); step(2); };
$("#skip1").onclick = () => { showSuggestions(); step(2); };

function showSuggestions() {
  if (!guess.titles?.length) return;
  $("#sug").innerHTML = `<span style="font-size:12.5px;color:var(--fg-3);align-self:center">From your CV:</span>` +
    guess.titles.map((t) => `<button data-t="${esc(t)}">+ ${esc(t)}</button>`).join("");
  $$("#sug button").forEach((b) => b.onclick = () => {
    const v = tagValues("titles");
    if (!v.includes(b.dataset.t)) fields.titles.values = [...v, b.dataset.t];
    b.remove();
  });
}

/* ── Step 2 ───────────────────────────────────────────────── */
$$("[data-tog]").forEach((t) => t.onclick = () => t.classList.toggle("on"));
$("#back2").onclick = () => step(1);
$("#next2").onclick = () => {
  if (!tagValues("titles").length) {
    document.querySelector('[data-tags="titles"] input').focus();
    return;
  }
  step(3);
};

/* ── Step 3 ───────────────────────────────────────────────── */
$("#industries").innerHTML = ALL_INDUSTRIES.map((i) => `<button class="pick" data-i="${i}">${i}</button>`).join("");
$$("#industries .pick").forEach((p) => p.onclick = () => p.classList.toggle("on"));
$("#back3").onclick = () => step(2);

$("#finish").onclick = async () => {
  const industries = $$("#industries .pick.on").map((p) => p.dataset.i);
  await store.saveProfile({
    titles: tagValues("titles"),
    locations: tagValues("locations").length ? tagValues("locations") : ["Remote"],
    industries,
    targets: pickCompanies(industries),
    remoteOnly: $('[data-tog="remoteOnly"]').classList.contains("on"),
    strictLocation: $('[data-tog="strictLocation"]').classList.contains("on"),
    languages: [navigator.language.slice(0, 2)],
  });

  step(4);
  const res = await chrome.runtime.sendMessage({ type: "scan" });

  if (res?.ok) {
    $("#done-h").textContent = res.matches ? `${res.matches} jobs match you` : "Search finished";
    $("#done-p").textContent = res.matches
      ? `Went through ${res.seen.toLocaleString()} postings in ${res.seconds} seconds. From now on this runs by itself, twice a day.`
      : "No matches yet with these filters. Try adding more job titles or widening your locations.";
  } else {
    $("#done-h").textContent = "Could not finish the first search";
    $("#done-p").textContent = res?.error || "Check your internet connection and try again from the dashboard.";
  }
  $("#open-app").style.display = "inline-flex";
  $("#open-app").onclick = () => location.href = "app.html";
};
