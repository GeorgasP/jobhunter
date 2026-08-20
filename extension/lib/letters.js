/*
 * Cover letters. Χωρίς κλειδί → σοβαρό template. Με κλειδί Anthropic → Claude.
 * Το κλειδί είναι του χρήστη, μένει στο chrome.storage του και πάει μόνο στο
 * api.anthropic.com.
 */

const SYSTEM = `You write high-converting cover letters for job seekers.

Rules:
1. Open with one specific sentence about THIS company and role.
2. Three concrete value propositions, each anchored to a fact from the CV.
3. Mirror the vocabulary of the job description.
4. Never invent experience the CV does not support.
5. 220-320 words. Plain text only, no markdown, no placeholders.
6. Write natively in the requested language.
7. No clichés: "hard worker", "team player", "passionate".`;

const LANG_NAMES = { en: "English", el: "Greek", es: "Spanish", de: "German",
  fr: "French", it: "Italian", pt: "Portuguese", nl: "Dutch", pl: "Polish" };

export async function generateLetter(job, profile, cv) {
  const lang = profile.language || "en";
  const cvText = (cv && cv.text) || "";

  if (profile.anthropicKey && (cvText || profile.about)) {
    try {
      return { text: await viaClaude(job, profile, cvText, lang), model: "claude" };
    } catch (e) {
      return { text: template(job, profile, cvText, lang), model: "template", error: String(e.message || e) };
    }
  }
  return { text: template(job, profile, cvText, lang), model: "template" };
}

async function viaClaude(job, profile, cvText, lang) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": profile.anthropicKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 1200,
      system: [{ type: "text", text: SYSTEM, cache_control: { type: "ephemeral" } }],
      messages: [{
        role: "user",
        content: `Write a cover letter in ${LANG_NAMES[lang] || "English"}.

COMPANY: ${job.company}
ROLE: ${job.title}
LOCATION: ${job.location || "n/a"}

JOB DESCRIPTION:
${(job.description || "").slice(0, 4000)}

CANDIDATE CV:
${cvText.slice(0, 8000)}
${profile.about ? `
IN THE CANDIDATE'S OWN WORDS:
${profile.about.slice(0, 1500)}
` : ""}
Return only the letter.`,
      }],
    }),
  });

  if (!res.ok) throw new Error(`Anthropic ${res.status}: ${(await res.text()).slice(0, 200)}`);
  const data = await res.json();
  const text = (data.content || []).filter((b) => b.type === "text").map((b) => b.text).join("\n").trim();
  if (!text) throw new Error("empty response");
  return text;
}

/* ── Template fallback ────────────────────────────────────── */

// Επικεφαλίδες και στοιχεία επικοινωνίας δεν είναι επιτεύγματα.
const NOISE = /@|https?:|linkedin|github|curriculum vitae|^\s*resume\b|\+\d{2}|\[.*\]/i;

/**
 * Τα bullets ενός CV σπάνε σε πολλές γραμμές, οπότε τα ξαναενώνουμε πρώτα.
 * Προτιμώνται πάντα οι γραμμές με πραγματικό bullet — εκεί είναι η ουσία.
 */
function highlights(cvText, n = 3) {
  const bullets = [];
  const fallback = [];
  let current = null;
  let currentIsBullet = false;

  const flush = () => {
    if (!current) return;
    const line = current.replace(/\*\*|`|_/g, "").replace(/\s+/g, " ").trim().replace(/[.;,]$/, "");
    current = null;
    if (line.length < 45 || line.length > 220 || line.endsWith(":") || NOISE.test(line)) return;
    (currentIsBullet ? bullets : fallback).push(line);
  };

  for (const raw of cvText.split(/\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || line.startsWith("---")) { flush(); continue; }

    const bulletMatch = /^[-*•●▪]\s+(.*)$/.exec(line);
    if (bulletMatch) {
      flush();
      current = bulletMatch[1];
      currentIsBullet = true;
    } else if (current) {
      current += " " + line;                       // συνέχεια της ίδιας γραμμής
    } else {
      current = line;
      currentIsBullet = false;
    }
    if (bullets.length >= n) break;
  }
  flush();

  return (bullets.length ? bullets : fallback).slice(0, n);
}

const T = {
  en: (c, t, h, name, contact) => [
    `Dear ${c} hiring team,`, "",
    `I am applying for the ${t} position. My background lines up closely with what the role asks for.`, "",
    ...(h.length ? h.map((x) => `• ${x}`) : ["• Please see my attached CV for the full background."]),
    "", `I would welcome the chance to discuss how I can contribute to ${c}. I am available for an interview at short notice.`,
    "", "Kind regards,", name, contact,
  ],
  el: (c, t, h, name, contact) => [
    `Αξιότιμοι κύριοι/κυρίες της ${c},`, "",
    `Γράφω για τη θέση ${t}. Το προφίλ μου ταιριάζει άμεσα με όσα ζητά ο ρόλος.`, "",
    ...(h.length ? h.map((x) => `• ${x}`) : ["• Παρακαλώ δείτε το συνημμένο βιογραφικό μου."]),
    "", `Θα χαρώ να συζητήσουμε πώς μπορώ να συνεισφέρω στην ${c}. Είμαι διαθέσιμος/η για συνέντευξη άμεσα.`,
    "", "Με εκτίμηση,", name, contact,
  ],
};

function template(job, profile, cvText, lang) {
  const make = T[lang] || T.en;
  const contact = [profile.email, profile.phone, profile.linkedin].filter(Boolean).join(" · ");
  return make(job.company, job.title, highlights(cvText), profile.name || "", contact)
    .join("\n").replace(/\n{3,}/g, "\n\n").trim();
}
