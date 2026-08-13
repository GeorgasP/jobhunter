/*
 * Μετατροπή νομισμάτων και περιόδων — μόνο για ΣΥΓΚΡΙΣΗ με το όριό σου.
 *
 * Η εμφάνιση μένει πάντα όπως το γράφει η αγγελία: «zł12.000 / month». Αυτό
 * που μετατρέπεται είναι το νούμερο πίσω από τα κουμπιά, ώστε το «ελάχιστο
 * €30.000/έτος» να συγκρίνεται σωστά με μισθό σε ζλότι ανά μήνα.
 *
 * Οι ισοτιμίες κατεβαίνουν μία φορά την ημέρα. Αν δεν κατέβουν (offline,
 * μπλοκαρισμένο δίκτυο), χρησιμοποιούνται οι ενσωματωμένες — καλύτερα κατά
 * προσέγγιση παρά καθόλου σύγκριση.
 */

const RATES_URL = "https://open.er-api.com/v6/latest/EUR";
const MAX_AGE_MS = 24 * 3600 * 1000;

/** Μονάδες ανά 1 EUR. Εφεδρικές τιμές, Αύγουστος 2026. */
export const FALLBACK_RATES = {
  EUR: 1, USD: 1.153, GBP: 0.854, CHF: 0.937, PLN: 4.305, SEK: 11.03,
  NOK: 11.6, DKK: 7.46, CZK: 24.6, RON: 5.08, HUF: 395, BGN: 1.956,
  TRY: 55.1, INR: 110.0, CAD: 1.607, AUD: 1.633, NZD: 1.79, JPY: 183.7,
  CNY: 8.2, SGD: 1.47, HKD: 8.99, AED: 4.24, SAR: 4.33, ILS: 4.1,
  BRL: 5.956, MXN: 21.3, ARS: 1180, CLP: 1080, COP: 4600, ZAR: 20.5,
  NGN: 1760, KES: 149, EGP: 56, PHP: 65, IDR: 18500, THB: 37.5,
  VND: 29000, MYR: 4.9, KRW: 1560, TWD: 35.6, UAH: 47, RSD: 117,
};

/** Πόσα «περίοδοι» σε έναν χρόνο. Γενναιόδωρα, για να μην κόβονται καλές θέσεις. */
const PER_YEAR = { year: 1, month: 12, week: 52, day: 250, hour: 2080 };

let rates = { ...FALLBACK_RATES };
let ratesDate = null;

export function setRates(next, date = null) {
  if (next && next.EUR) { rates = next; ratesDate = date; }
}
export const getRatesInfo = () => ({ date: ratesDate, count: Object.keys(rates).length });

/** Ετησιοποίηση: €3.500/μήνα → €42.000/έτος. */
export function annualize(amount, period = "year") {
  if (!amount) return null;
  return Math.round(amount * (PER_YEAR[period] || 1));
}

/** Μετατροπή ποσού μεταξύ ISO κωδικών. Άγνωστο νόμισμα → επιστρέφει ως έχει. */
export function convert(amount, from, to) {
  if (!amount) return null;
  const a = rates[String(from || "").toUpperCase()];
  const b = rates[String(to || "").toUpperCase()];
  if (!a || !b) return amount;
  return Math.round((amount / a) * b);
}

/** Ετήσιο ποσό στο νόμισμα του χρήστη — ό,τι χρειάζεται η σύγκριση. */
export function annualIn(amount, currency, period, targetCurrency) {
  const yearly = annualize(amount, period);
  return yearly == null ? null : convert(yearly, currency || targetCurrency, targetCurrency);
}

/** Κατεβάζει ισοτιμίες το πολύ μία φορά την ημέρα, με cache στο storage. */
export async function refreshRates(storage = chrome.storage?.local) {
  try {
    const cached = storage ? (await storage.get("fx")).fx : null;
    if (cached?.rates && Date.now() - (cached.at || 0) < MAX_AGE_MS) {
      setRates(cached.rates, cached.date);
      return { ok: true, cached: true, date: cached.date };
    }

    const res = await fetch(RATES_URL, { headers: { accept: "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const next = data.rates || data.conversion_rates;
    if (!next?.USD) throw new Error("unexpected shape");

    const date = data.time_last_update_utc?.slice(5, 16) || new Date().toISOString().slice(0, 10);
    setRates(next, date);
    if (storage) await storage.set({ fx: { rates: next, date, at: Date.now() } });
    return { ok: true, cached: false, date };
  } catch (e) {
    // Μένουμε στις ενσωματωμένες — η σύγκριση δεν σταματάει ποτέ.
    return { ok: false, error: String(e.message || e) };
  }
}
