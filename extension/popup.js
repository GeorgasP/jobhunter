import * as store from "./lib/store.js";

const $ = (s) => document.querySelector(s);

chrome.storage.local.get("theme").then(({ theme }) => {
  if (theme) document.documentElement.dataset.theme = theme;
});

async function paint() {
  const [jobs, apps, state, res] = await Promise.all([
    store.getJobs(), store.getApps(), store.getState(),
    chrome.runtime.sendMessage({ type: "matches" }),
  ]);
  $("#m").textContent = res?.matches?.length ?? 0;
  $("#a").textContent = apps.length;
  $("#j").textContent = jobs.length;

  if (!state.lastScan) {
    $("#last").textContent = "not searched yet";
  } else {
    const mins = Math.round((Date.now() - Date.parse(state.lastScan)) / 60000);
    $("#last").textContent = mins < 60 ? `last search ${mins} min ago`
      : `last search ${Math.round(mins / 60)}h ago`;
  }
}

$("#open").onclick = async () => {
  const onboarded = await store.isOnboarded();
  chrome.tabs.create({ url: chrome.runtime.getURL(onboarded ? "app.html" : "onboarding.html") });
  window.close();
};

$("#scan").onclick = async () => {
  const btn = $("#scan");
  btn.disabled = true;
  btn.textContent = "Searching…";
  const res = await chrome.runtime.sendMessage({ type: "scan" });
  btn.disabled = false;
  btn.textContent = res?.ok ? `Found ${res.added} new` : "Scan failed";
  paint();
};

paint();
