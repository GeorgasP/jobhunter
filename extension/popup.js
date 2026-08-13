import * as store from "./lib/store.js";
import { initI18n, t } from "./lib/i18n.js";

const $ = (s) => document.querySelector(s);

chrome.storage.local.get("theme").then(({ theme }) => {
  if (theme) document.documentElement.dataset.theme = theme;
});
store.getProfile().then((p) => initI18n(p.uiLanguage).then(paint));

async function paint() {
  const [jobs, apps, state, res] = await Promise.all([
    store.getJobs(), store.getApps(), store.getState(),
    chrome.runtime.sendMessage({ type: "matches" }),
  ]);
  $("#m").textContent = res?.matches?.length ?? 0;
  $("#a").textContent = apps.length;
  $("#j").textContent = jobs.length;

  if (!state.lastScan) {
    $("#last").textContent = t("popup.notSearched");
  } else {
    const mins = Math.round((Date.now() - Date.parse(state.lastScan)) / 60000);
    $("#last").textContent = mins < 60 ? t("popup.lastSearchMin", { n: mins })
      : t("popup.lastSearchHours", { n: Math.round(mins / 60) });
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
  btn.textContent = t("popup.searching");
  const res = await chrome.runtime.sendMessage({ type: "scan" });
  btn.disabled = false;
  btn.textContent = res?.ok ? t("popup.foundNew", { n: res.added }) : t("popup.failed");
  paint();
};
