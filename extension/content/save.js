/*
 * «Αποθήκευση στο JobHunter» — για αγγελίες που δεν έχουν API.
 *
 * Πολλές θέσεις ανεβαίνουν μόνο σε ανάρτηση: ομάδα στο Facebook, νήμα στο
 * Reddit, δημοσίευση σε σελίδα. Καμία σάρωση δεν τις φτάνει, και κανένα
 * API δεν τις δίνει.
 *
 * Το script ΔΕΝ ψάχνει και ΔΕΝ στέλνει τίποτα από μόνο του. Εμφανίζει ένα
 * κουμπί όταν η σελίδα που κοιτάς μοιάζει με αγγελία, και μόνο αν το πατήσεις
 * διαβάζει το κείμενο και το στέλνει στο extension. Είναι η διαφορά ανάμεσα
 * στο να κρατάς σημείωση για κάτι που βλέπεις και στο να σαρώνεις έναν ιστότοπο.
 */
(function () {
  "use strict";
  if (window.__jobhunterSave) return;
  window.__jobhunterSave = true;

  const HIRING = [
    // αγγλικά
    "hiring", "we are looking for", "we're looking for", "job opening", "vacancy",
    "apply now", "job offer", "now hiring", "join our team", "position available",
    "send your cv", "send cv", "recruiting",
    // ελληνικά
    "ζητείται", "ζητούνται", "αναζητούμε", "αναζητείται", "θέση εργασίας",
    "θέσεις εργασίας", "προσλαμβάνουμε", "αποστολή βιογραφικών", "βιογραφικό",
    "ζητάμε", "προσφέρεται εργασία",
  ];

  const textOf = (el) => (el?.innerText || "").replace(/\s+/g, " ").trim();

  /** Το πιο πιθανό μπλοκ αγγελίας: το μικρότερο που περιέχει ένδειξη πρόσληψης. */
  function findPosting() {
    const sel = String(window.getSelection() || "").trim();
    if (sel.length > 80) return { text: sel, node: null };

    const candidates = [...document.querySelectorAll(
      "article, [role=article], [data-testid=post_message], .userContent, " +
      ".feed-shared-update-v2, .Post, .usertext-body, main, section")];
    let best = null;
    for (const el of candidates) {
      const t = textOf(el);
      if (t.length < 120 || t.length > 6000) continue;
      const low = t.toLowerCase();
      if (!HIRING.some((k) => low.includes(k))) continue;
      if (!best || t.length < best.text.length) best = { text: t, node: el };
    }
    return best;
  }

  function guess(text) {
    const lines = text.split(/[\n·|]|(?<=[.!?])\s+/).map((s) => s.trim()).filter(Boolean);
    const fits = (l) => l.length >= 8 && l.length <= 110;
    // Ο ρόλος είναι στη γραμμή που λέει ότι ψάχνουν κάποιον — όχι στην πρώτη,
    // που συνήθως είναι το όνομα της σελίδας που δημοσίευσε.
    const hiring = lines.find((l) => fits(l) && HIRING.some((k) => l.toLowerCase().includes(k)));
    const title = hiring || lines.find(fits) || lines[0] || "";
    const email = (text.match(/[\w.+-]+@[\w-]+\.[\w.]{2,}/) || [])[0] || "";
    // Οι αναρτήσεις ξεκινούν με χρονόσημο («3 ώρες», «2h», «πριν 5 λεπτά»),
    // που δεν είναι μέρος του τίτλου.
    const clean = title
      // \w δεν πιάνει ελληνικά· χρειάζεται \p{L} με τη σημαία u.
      .replace(/^(πριν\s+)?\d+\s*(ώρ\p{L}*|λεπτ\p{L}*|ημέρ\p{L}*|h|hr|hrs|min|days?)\s*/iu, "")
      .replace(/^[-–—:·,\s]+/, "")
      .trim();
    return { title: clean.slice(0, 120), email };
  }

  let panel = null;

  function close() {
    panel?.remove();
    panel = null;
  }

  function openForm(found) {
    close();
    const g = guess(found.text);
    panel = document.createElement("div");
    panel.id = "__jobhunter_save_panel";
    panel.attachShadow({ mode: "open" }).innerHTML = `
      <style>
        :host { all: initial; }
        .box {
          position: fixed; z-index: 2147483647; right: 18px; bottom: 74px;
          width: 330px; padding: 16px 16px 14px;
          background: #101827; color: #f1f5f9;
          border: 1px solid #344863; border-radius: 12px;
          box-shadow: 0 12px 40px -12px rgba(0,0,0,.7);
          font: 13.5px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        b { display: block; margin-bottom: 10px; font-size: 14px; }
        label { display: block; margin-top: 9px; font-size: 11.5px;
                letter-spacing: .4px; text-transform: uppercase; color: #899bb2; }
        input, textarea {
          width: 100%; margin-top: 4px; padding: 7px 9px;
          background: #0c1526; color: #f1f5f9;
          border: 1px solid #344863; border-radius: 7px;
          font: inherit; box-sizing: border-box;
        }
        textarea { height: 62px; resize: vertical; }
        .row { display: flex; gap: 8px; margin-top: 13px; }
        button {
          flex: 1; padding: 8px 10px; border: 1px solid #344863; border-radius: 8px;
          background: #162033; color: #f1f5f9; font: inherit; cursor: pointer;
        }
        button.primary { background: #2563eb; border-color: #2563eb; color: #fff; font-weight: 600; }
        .hint { margin-top: 9px; font-size: 11.5px; color: #899bb2; }
      </style>
      <div class="box">
        <b>Αποθήκευση αγγελίας</b>
        <label>Τίτλος</label><input id="t" value="">
        <label>Εταιρεία / σελίδα</label><input id="c" value="">
        <label>Περιοχή</label><input id="l" value="">
        <label>Κείμενο</label><textarea id="d"></textarea>
        <div class="row">
          <button id="cancel">Άκυρο</button>
          <button id="save" class="primary">Αποθήκευση</button>
        </div>
        <div class="hint" id="hint"></div>
      </div>`;
    document.documentElement.appendChild(panel);

    const $ = (s) => panel.shadowRoot.querySelector(s);
    $("#t").value = g.title;
    $("#c").value = document.title.split(/[|\-–]/)[0].trim().slice(0, 60);
    $("#d").value = found.text.slice(0, 1500);
    $("#hint").textContent = g.email ? `Επικοινωνία: ${g.email}` : "";

    $("#cancel").onclick = close;
    $("#save").onclick = () => {
      $("#save").disabled = true;
      chrome.runtime.sendMessage({
        type: "saveJob",
        job: {
          title: $("#t").value.trim(),
          company: $("#c").value.trim(),
          location: $("#l").value.trim(),
          description: $("#d").value.trim(),
          url: location.href,
          contactEmail: g.email,
        },
      }, (res) => {
        $("#hint").textContent = res?.ok
          ? "Αποθηκεύτηκε. Θα το βρεις στα Ευρήματα."
          : `Δεν αποθηκεύτηκε: ${res?.error || "άγνωστο σφάλμα"}`;
        if (res?.ok) setTimeout(close, 1400);
        else $("#save").disabled = false;
      });
    };
  }

  function mountTrigger() {
    const found = findPosting();
    if (!found) return;
    if (document.getElementById("__jobhunter_save_btn")) return;

    const b = document.createElement("button");
    b.id = "__jobhunter_save_btn";
    b.type = "button";
    b.textContent = "🎯 Αποθήκευση στο JobHunter";
    b.style.cssText = [
      "position:fixed", "z-index:2147483646", "right:18px", "bottom:18px",
      "padding:10px 14px", "border:0", "border-radius:10px",
      "background:#2563eb", "color:#fff", "font:600 13px/1 system-ui,sans-serif",
      "box-shadow:0 6px 22px -6px rgba(0,0,0,.6)", "cursor:pointer",
    ].join(";");
    b.onclick = () => openForm(findPosting() || found);
    document.documentElement.appendChild(b);
  }

  // Οι σελίδες κοινωνικών δικτύων φορτώνουν περιεχόμενο συνέχεια· κοιτάμε ξανά
  // όταν αλλάζει κάτι, αλλά με φρένο ώστε να μη ζορίζουμε τη σελίδα.
  let timer = null;
  const recheck = () => {
    clearTimeout(timer);
    timer = setTimeout(mountTrigger, 900);
  };
  recheck();
  new MutationObserver(recheck).observe(document.documentElement,
    { childList: true, subtree: true });
})();
