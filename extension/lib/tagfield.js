/*
 * Πεδίο με ετικέτες + autocomplete.
 *
 * Χρησιμοποιείται και στο onboarding και στις ρυθμίσεις — μία υλοποίηση, ίδια
 * συμπεριφορά. Ο χρήστης μπορεί πάντα να γράψει ό,τι θέλει· οι προτάσεις είναι
 * βοήθεια, όχι φράχτης.
 */
import { search } from "./suggest.js";

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

export function createTagField(box, { values = [], vocabulary = () => [], onChange } = {}) {
  const input = box.querySelector("input");
  let current = [...values];
  let items = [];
  let highlighted = -1;

  const panel = document.createElement("div");
  panel.className = "sugbox";
  box.appendChild(panel);

  const commit = () => {
    box.dataset.values = JSON.stringify(current);
    if (onChange) onChange(current);
  };

  function renderTags() {
    box.querySelectorAll(".t").forEach((t) => t.remove());
    for (const value of current) {
      const tag = document.createElement("span");
      tag.className = "t";
      tag.innerHTML = `${esc(value)} <b>×</b>`;
      tag.querySelector("b").onclick = (e) => {
        e.stopPropagation();
        current = current.filter((v) => v !== value);
        renderTags(); commit();
      };
      box.insertBefore(tag, input);
    }
    commit();
  }

  const add = (value) => {
    const v = (value || "").trim();
    if (!v) return;
    if (!current.some((x) => x.toLowerCase() === v.toLowerCase())) current.push(v);
    input.value = "";
    close();
    renderTags();
  };

  function close() {
    panel.classList.remove("on");
    highlighted = -1;
    items = [];
  }

  function paint() {
    if (!items.length) { close(); return; }
    panel.innerHTML = items.map((it, i) => `
      <div class="s ${i === highlighted ? "hi" : ""}" data-i="${i}">
        <em>${esc(it.label)}</em>
        <span>${it.count ? `${it.count} posting${it.count === 1 ? "" : "s"}` : "suggestion"}</span>
      </div>`).join("");
    panel.classList.add("on");
    panel.querySelectorAll(".s").forEach((el) => {
      el.onmousedown = (e) => { e.preventDefault(); add(items[Number(el.dataset.i)].label); };
    });
  }

  function refresh() {
    const query = input.value.trim();
    const chosen = new Set(current.map((c) => c.toLowerCase()));
    items = search(vocabulary(), query, 8).filter((it) => !chosen.has(it.label.toLowerCase()));
    highlighted = items.length && query ? 0 : -1;
    paint();
  }

  input.addEventListener("input", refresh);
  input.addEventListener("focus", refresh);
  input.addEventListener("blur", () => setTimeout(close, 120));

  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!items.length) return;
      e.preventDefault();
      highlighted = (highlighted + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      paint();
      return;
    }
    if (e.key === "Enter" || e.key === "Tab" || e.key === ",") {
      // Enter σε τονισμένη πρόταση → η γραφή των αγγελιών. Αλλιώς ό,τι έγραψες.
      if (highlighted >= 0 && items[highlighted]) {
        e.preventDefault();
        add(items[highlighted].label);
      } else if (input.value.trim()) {
        e.preventDefault();
        add(input.value);
      }
      return;
    }
    if (e.key === "Escape") { close(); return; }
    if (e.key === "Backspace" && !input.value && current.length) {
      current.pop();
      renderTags();
    }
  });

  box.addEventListener("click", (e) => { if (e.target === box) input.focus(); });

  renderTags();

  return {
    get values() { return [...current]; },
    set values(next) { current = [...next]; renderTags(); },
  };
}
