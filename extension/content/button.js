/*
 * Το πλωτό κουμπί στη σελίδα της αίτησης.
 * Τα δεδομένα έρχονται από τον service worker — καμία σύνδεση με σέρβερ.
 */
(function () {
  "use strict";
  if (window.__jobhunterButton) return;
  window.__jobhunterButton = true;

  const looksLikeForm = () =>
    Boolean(document.querySelector("input[type=file]")) ||
    document.querySelectorAll("input[type=text], input[type=email], textarea").length >= 3;

  function makeButton() {
    const b = document.createElement("button");
    b.id = "__jobhunter_btn";
    b.type = "button";
    b.textContent = "🎯 Fill with JobHunter";
    b.style.cssText = [
      "position:fixed", "z-index:2147483646", "right:18px", "bottom:18px",
      "background:linear-gradient(135deg,#5b8cff,#7c5cff)", "color:#fff", "border:none",
      "border-radius:10px", "padding:11px 16px", "cursor:pointer",
      "font:600 14px/1 -apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif",
      "box-shadow:0 6px 22px rgba(91,140,255,.4)",
    ].join(";");

    b.addEventListener("click", () => {
      b.disabled = true;
      b.textContent = "Filling…";
      chrome.runtime.sendMessage({ type: "prefill", url: location.href }, (data) => {
        b.disabled = false;
        b.textContent = "🎯 Fill with JobHunter";
        if (!data || !data.ok) {
          alert("JobHunter: " + ((data && data.error) || "no response"));
          return;
        }
        const report = window.__jobhunterFill(data);
        if (!report.filled && !report.cv) {
          alert("JobHunter did not recognise any fields on this page.");
          return;
        }
        // Μόλις ο χρήστης πατήσει submit, σημειώνουμε την αίτηση ως σταλμένη.
        document.addEventListener("click", (e) => {
          const el = e.target.closest("button,input[type=submit]");
          if (!el) return;
          const label = (el.value || el.textContent || "").toLowerCase();
          if (/submit|apply|send|υποβολ|enviar|bewerb/.test(label)) {
            chrome.runtime.sendMessage({ type: "markSent", applicationId: data.applicationId });
          }
        }, { capture: true, once: true });
      });
    });
    return b;
  }

  function mount() {
    if (document.getElementById("__jobhunter_btn") || !looksLikeForm()) return;
    document.body.appendChild(makeButton());
  }

  mount();
  new MutationObserver(mount).observe(document.documentElement, { childList: true, subtree: true });
  setTimeout(mount, 1500);
  setTimeout(mount, 4000);
})();
