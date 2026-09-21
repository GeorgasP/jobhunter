/*
 * JobHunter — form autofill.
 *
 * Τρέχει στη σελίδα της αίτησης (bookmarklet ή extension content script) και
 * γεμίζει τη φόρμα από το προφίλ του χρήστη. ΔΕΝ πατάει ποτέ Submit: η υποβολή
 * μένει πάντα ανθρώπινη απόφαση.
 *
 * Εκτίθεται ως window.__jobhunterFill(data) -> report
 */
(function () {
  "use strict";

  // ── Native setters: τα React/Vue controlled inputs αγνοούν το el.value = x ──
  function setNativeValue(el, value) {
    const proto = el instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
    if (setter) setter.call(el, value); else el.value = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    el.dispatchEvent(new Event("blur", { bubbles: true }));
  }

  // ── Όλο το κείμενο που περιγράφει ένα πεδίο ──
  function describe(el) {
    const bits = [el.name, el.id, el.placeholder, el.getAttribute("aria-label"),
                  el.getAttribute("autocomplete"), el.getAttribute("data-testid")];

    if (el.id) {
      const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (lbl) bits.push(lbl.textContent);
    }
    const wrapper = el.closest("label");
    if (wrapper) bits.push(wrapper.textContent);

    const labelledBy = el.getAttribute("aria-labelledby");
    if (labelledBy) {
      labelledBy.split(/\s+/).forEach((id) => {
        const node = document.getElementById(id);
        if (node) bits.push(node.textContent);
      });
    }
    // Greenhouse/Lever βάζουν το label σε γονικό div πάνω από το input
    const field = el.closest("div,fieldset,li,section");
    if (field) {
      const head = field.querySelector("label,legend,.label,[class*='label']");
      if (head) bits.push(head.textContent);
    }
    return bits.filter(Boolean).join(" ").toLowerCase().replace(/\s+/g, " ").slice(0, 300);
  }

  // ── Κανόνες: πρώτο match κερδίζει, γι' αυτό τα ειδικά πάνω ──
  const RULES = [
    [/first.?name|given.?name|forename|vorname|prénom|nombre\b/, "first_name"],
    [/last.?name|surname|family.?name|nachname|apellido/, "last_name"],
    [/full.?name|^name$|\bname\b(?!.*(company|school|university|reference|file))/, "full_name"],
    [/e-?mail/, "email"],
    [/phone|mobile|telephone|contact number|τηλέφων/, "phone"],
    [/linked.?in/, "linkedin"],
    [/git.?hub/, "github"],
    // Το Lever ονομάζει κάθε πεδίο συνδέσμου «… URL» — «LinkedIn URL», «Video
    // Link URL». Χωρίς την εξαίρεση, το προφίλ σου κατέληγε και στη θέση όπου ο
    // εργοδότης περίμενε βίντεο.
    [/video|reel|showreel|demo ?tape/, null],
    [/portfolio|personal (web)?site|website|\burl\b|blog/, "website"],
    [/current (city|location)|where are you (based|located)|city|location|address|town/, "location"],
    [/salary|compensation|expected pay|rate expectation|μισθ/, "salary_expectation"],
    [/notice period|when can you start|start date|availability|available from/, "notice_period"],
    [/work (authorization|authorisation|permit|status)|legally (authorized|entitled)|visa|sponsorship|right to work/, "work_authorization"],
    [/how did you (hear|find)|referral source|source/, "how_did_you_hear"],
    [/cover ?letter|why do you|why are you|motivation|tell us|message|additional information|anything else/, "cover_letter"],
  ];

  function keyFor(el) {
    const type = (el.type || "").toLowerCase();
    if (type === "email") return "email";
    if (type === "tel") return "phone";
    const text = describe(el);
    // Το key μπορεί να είναι null: κανόνας-εξαίρεση που λέει «μην αγγίξεις».
    for (const [re, key] of RULES) if (re.test(text)) return key;
    if (type === "url") return "website";
    return null;
  }

  function isFillable(el) {
    if (el.disabled || el.readOnly) return false;
    if (el.offsetParent === null && el.type !== "file") return false;   // κρυφό
    const type = (el.type || "").toLowerCase();
    if (el.tagName === "TEXTAREA") return true;
    return ["text", "email", "tel", "url", "search", ""].includes(type);
  }

  // ── Επισύναψη CV: File + DataTransfer, ο μόνος τρόπος από JS ──
  function attachCV(input, cv) {
    try {
      const bytes = Uint8Array.from(atob(cv.base64), (c) => c.charCodeAt(0));
      const file = new File([bytes], cv.filename, { type: cv.mime || "application/octet-stream" });
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    } catch (e) {
      return false;
    }
  }

  /*
   * Πόσα υποχρεωτικά μένουν αναπάντητα.
   *
   * Δύο παγίδες: το Workable βάζει aria-required σε wrapper div, όχι στο πεδίο,
   * οπότε μετράμε μόνο πραγματικά controls και κοιτάμε αν κάποιος γονιός τα
   * δηλώνει υποχρεωτικά· και μια ομάδα από πέντε ραδιοπλήκτρα είναι μία
   * ερώτηση, όχι πέντε.
   */
  function countUnanswered() {
    const seenGroups = new Set();
    return [...document.querySelectorAll("input, textarea, select")].filter((el) => {
      if (el.disabled || el.offsetParent === null) return false;
      if (!(el.required || el.getAttribute("aria-required") === "true"
            || el.closest("[aria-required='true']"))) return false;

      const type = (el.type || "").toLowerCase();
      if (type === "file") return el.files.length === 0;
      if (type === "radio" || type === "checkbox") {
        const group = el.name || el.id;
        if (!group || seenGroups.has(group)) return false;
        seenGroups.add(group);
        return !document.querySelector(`[name="${CSS.escape(group)}"]:checked`);
      }
      return !String(el.value || "").trim();
    }).length;
  }

  function toast(report, job) {
    document.getElementById("__jobhunter_toast")?.remove();
    const box = document.createElement("div");
    box.id = "__jobhunter_toast";
    box.style.cssText = [
      "position:fixed", "z-index:2147483647", "right:18px", "bottom:18px",
      "max-width:330px", "background:#161b22", "color:#e6edf3",
      "border:1px solid #2f81f7", "border-radius:10px", "padding:14px 16px",
      "font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif",
      "box-shadow:0 8px 28px rgba(0,0,0,.45)",
    ].join(";");
    const missing = report.skipped.length
      ? `<div style="color:#8b949e;font-size:12.5px;margin-top:8px">Left for you: ${report.skipped.join(", ")}</div>`
      : "";
    // Οι δοκιμιακές ερωτήσεις («περίγραψε τον καλύτερο μηχανικό που δούλεψες
    // μαζί») δεν συμπληρώνονται ποτέ από εργαλείο. Αν δεν τις μετρήσουμε, το
    // «3 πεδία συμπληρώθηκαν» ακούγεται σαν τελείωσες, και δεν τελείωσες.
    const required = report.required
      ? `<div style="color:#f0a020;font-size:12.5px;margin-top:6px">${report.required} required field${
          report.required === 1 ? " still needs" : "s still need"} you</div>`
      : "";
    box.innerHTML =
      `<b>🎯 JobHunter</b><br>${report.filled} field${report.filled === 1 ? "" : "s"} filled` +
      (report.cv ? " · CV attached" : "") +
      required +
      `<div style="color:#8b949e;font-size:12.5px;margin-top:6px">${job ? job.company + " — " + job.title : ""}</div>` +
      `<div style="margin-top:8px;font-size:12.5px">Check everything, then press Submit yourself.</div>` +
      missing;
    document.body.appendChild(box);
    setTimeout(() => box.remove(), 12000);
  }

  window.__jobhunterFill = function (data) {
    const answers = data.answers || {};
    if (data.cover_letter) answers.cover_letter = data.cover_letter;

    const report = { filled: 0, cv: false, fields: [], skipped: [] };
    const seen = new Set();

    document.querySelectorAll("input, textarea").forEach((el) => {
      if ((el.type || "").toLowerCase() === "file") {
        if (!report.cv && data.cv && /resume|cv|attach|upload|file/.test(describe(el) + " " + el.name)) {
          report.cv = attachCV(el, data.cv);
        }
        return;
      }
      if (!isFillable(el)) return;

      const key = keyFor(el);
      if (!key) return;

      // full_name μόνο αν δεν υπάρχει ήδη ζεύγος first/last
      if (key === "full_name" && seen.has("first_name")) return;

      // Μία φορά το καθένα. Μια φόρμα με τρία πεδία συνδέσμου δεν θέλει το ίδιο
      // προφίλ τρεις φορές — φαίνεται προχειρότητα σε όποιον το διαβάσει. Μόνη
      // εξαίρεση η επιβεβαίωση, όπου η επανάληψη είναι το ζητούμενο.
      if (seen.has(key) && !/confirm|repeat|verify|again|ξανά/.test(describe(el))) return;

      const value = answers[key];
      if (!value) return;
      if (el.value && el.value.trim()) return;          // μη γράφεις πάνω στον χρήστη

      setNativeValue(el, value);
      seen.add(key);
      report.filled++;
      report.fields.push(key);
    });

    // Τι έμεινε: selects/radios (work authorization, relocation) — δεν τα
    // αγγίζουμε, γιατί λάθος επιλογή σε νομική ερώτηση κοστίζει.
    document.querySelectorAll("select, input[type=radio], input[type=checkbox]").forEach((el) => {
      if (el.disabled || el.offsetParent === null) return;
      const text = describe(el);
      for (const [re, key] of RULES) {
        if (!re.test(text)) continue;
        // Ό,τι συμπληρώθηκε ήδη δεν «έμεινε σε σένα». Τα ραδιοπλήκτρα των
        // αντωνυμιών περιέχουν το όνομα, και το μήνυμα έλεγε ότι έμεινε το
        // όνομα αφού το είχε μόλις γράψει.
        if (key && !seen.has(key) && !report.skipped.includes(key)) report.skipped.push(key);
        break;
      }
    });

    if (data.cv && !report.cv) report.skipped.push("CV upload");

    report.required = countUnanswered();

    toast(report, data.job);
    return report;
  };

  return window.__jobhunterFill;
})();
