/*
 * Μεταφράσεις.
 *
 * Το ενσωματωμένο i18n του Chrome ακολουθεί υποχρεωτικά τη γλώσσα του browser
 * και δεν αφήνει τον χρήστη να διαλέξει άλλη. Επειδή θέλουμε ρητή επιλογή,
 * φορτώνουμε μόνοι μας τα λεξικά από το locales/.
 *
 * Πρώτη φορά: μαντεύουμε από τον browser. Μετά: ό,τι διάλεξε ο χρήστης.
 */

export const LANGUAGES = [
  { code: "en", name: "English",    english: "English" },
  { code: "el", name: "Ελληνικά",   english: "Greek" },
  { code: "es", name: "Español",    english: "Spanish" },
  { code: "de", name: "Deutsch",    english: "German" },
  { code: "fr", name: "Français",   english: "French" },
  { code: "it", name: "Italiano",   english: "Italian" },
  { code: "pt", name: "Português",  english: "Portuguese" },
  { code: "pl", name: "Polski",     english: "Polish" },
];

const SUPPORTED = new Set(LANGUAGES.map((l) => l.code));
const DEFAULT = "en";

let strings = {};
let fallback = {};
let current = DEFAULT;

/** Το background τρέχει σε service worker: δεν υπάρχει document εκεί. */
const hasDOM = () => typeof document !== "undefined";

/** Η γλώσσα του browser, αν την υποστηρίζουμε. */
export function detectLanguage() {
  const candidates = [];
  try { candidates.push(chrome.i18n?.getUILanguage?.()); } catch { /* εκτός extension */ }
  candidates.push(navigator.language, ...(navigator.languages || []));

  for (const raw of candidates) {
    const base = String(raw || "").toLowerCase().split("-")[0];
    if (SUPPORTED.has(base)) return base;
  }
  return DEFAULT;
}

async function fetchLocale(code) {
  const url = (typeof chrome !== "undefined" && chrome.runtime?.getURL)
    ? chrome.runtime.getURL(`locales/${code}.json`)
    : `locales/${code}.json`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`locale ${code}: HTTP ${res.status}`);
  return res.json();
}

/** Φορτώνει μια γλώσσα. Τα αγγλικά μένουν πάντα ως δίχτυ για κλειδιά που λείπουν. */
export async function loadLanguage(code) {
  const wanted = SUPPORTED.has(code) ? code : DEFAULT;

  if (!Object.keys(fallback).length) {
    fallback = await fetchLocale(DEFAULT).catch(() => ({}));
  }
  strings = wanted === DEFAULT ? fallback : await fetchLocale(wanted).catch(() => ({}));
  current = wanted;
  // Ο service worker δεν έχει DOM· το ίδιο αρχείο τρέχει και εκεί (για τα
  // κείμενα των ειδοποιήσεων) και στις σελίδες.
  if (hasDOM()) document.documentElement?.setAttribute("lang", wanted);
  return wanted;
}

export const currentLanguage = () => current;

/**
 * t("cards.apply") → «Apply»
 * t("scan.done", { seen: 2011, added: 62 }) → αντικαθιστά τα {seen} κ.λπ.
 * Κλειδί που λείπει επιστρέφει το αγγλικό, και σε έσχατη ανάγκη το ίδιο το κλειδί
 * — ποτέ κενή οθόνη.
 */
export function t(key, vars) {
  let text = strings[key] ?? fallback[key] ?? key;
  if (vars) {
    for (const [name, value] of Object.entries(vars)) {
      text = text.replaceAll(`{${name}}`, String(value));
    }
  }
  return text;
}

/** Εφαρμόζει τις μεταφράσεις σε ό,τι έχει data-i18n στο DOM. */
export function applyTranslations(root) {
  const scope = root || (hasDOM() ? document : null);
  if (!scope) return;                       // service worker: τίποτα να βάψουμε
  scope.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  scope.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPh);
  });
  scope.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.title = t(el.dataset.i18nTitle);
  });
  scope.querySelectorAll("[data-i18n-html]").forEach((el) => {
    el.innerHTML = t(el.dataset.i18nHtml);
  });
  const title = scope.querySelector?.("title[data-i18n-doc]");
  if (title && hasDOM()) document.title = t(title.dataset.i18nDoc);
}

/**
 * Ξεκινά τη μετάφραση: παίρνει την αποθηκευμένη επιλογή, αλλιώς μαντεύει.
 * Επιστρέφει τον κωδικό που τελικά χρησιμοποιείται.
 */
export async function initI18n(saved) {
  const code = saved && SUPPORTED.has(saved) ? saved : detectLanguage();
  await loadLanguage(code);
  applyTranslations();
  return code;
}
