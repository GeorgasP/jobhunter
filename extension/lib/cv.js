import { ALL_PROFESSIONS } from "./professions.js";

/*
 * CV upload + parsing, χωρίς καμία εξωτερική βιβλιοθήκη.
 *
 * PDF  : αποσυμπίεση των FlateDecode streams με DecompressionStream και
 *        εξαγωγή των Tj/TJ strings.
 * DOCX : το .docx είναι zip — διαβάζουμε το word/document.xml απευθείας.
 * TXT/MD: ό,τι βλέπεις.
 *
 * Από το κείμενο βγάζουμε όνομα, email, τηλέφωνο, LinkedIn και πιθανούς
 * τίτλους θέσεων, ώστε το onboarding να είναι σχεδόν αυτόματο.
 */

export const MAX_CV_BYTES = 8 * 1024 * 1024;

const dec = new TextDecoder("utf-8", { fatal: false });
const latin = new TextDecoder("latin1");

async function inflate(bytes, format) {
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream(format));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/* ── PDF ──────────────────────────────────────────────────── */

/**
 * Δύο κόσμοι σε ένα format:
 *
 *  • Απλά PDF (base-14 γραμματοσειρές): τα bytes μέσα στις παρενθέσεις ΕΙΝΑΙ
 *    το κείμενο. Το διαβάζεις κατευθείαν.
 *  • Σύγχρονα PDF (Word, Google Docs, LaTeX, Chrome): ενσωματώνουν υποσύνολα
 *    γραμματοσειρών με Identity encoding — τα bytes είναι αριθμοί glyph, όχι
 *    γράμματα. Η αντιστοίχιση σε κείμενο ζει σε ένα /ToUnicode CMap ανά
 *    γραμματοσειρά. Χωρίς αυτό, βγάζεις σκουπίδια.
 *
 * Διαβάζουμε και τα δύο.
 */

const hexToText = (hex) => {
  let out = "";
  for (let i = 0; i + 3 < hex.length; i += 4) out += String.fromCharCode(parseInt(hex.slice(i, i + 4), 16));
  return out;
};

function parseCMap(text) {
  const map = new Map();

  for (const block of text.matchAll(/beginbfchar([\s\S]*?)endbfchar/g)) {
    for (const e of block[1].matchAll(/<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>/g)) {
      map.set(parseInt(e[1], 16), hexToText(e[2]));
    }
  }

  for (const block of text.matchAll(/beginbfrange([\s\S]*?)endbfrange/g)) {
    const body = block[1];
    // <lo> <hi> [ <u1> <u2> … ]
    for (const e of body.matchAll(/<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[([\s\S]*?)\]/g)) {
      let code = parseInt(e[1], 16);
      for (const u of e[3].matchAll(/<([0-9A-Fa-f]+)>/g)) map.set(code++, hexToText(u[1]));
    }
    // <lo> <hi> <firstUnicode>
    for (const e of body.matchAll(/<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>(?!\s*\[)/g)) {
      const lo = parseInt(e[1], 16), hi = parseInt(e[2], 16), dst = parseInt(e[3], 16);
      for (let c = lo; c <= hi && c - lo < 65536; c++) map.set(c, String.fromCodePoint(dst + (c - lo)));
    }
  }
  return map;
}

/** Αποσυμπιέζει το stream ενός αντικειμένου, αν έχει. */
async function objectStream(bytes, raw, from, to) {
  const head = raw.indexOf("stream", from);
  if (head < 0 || head > to) return null;
  let start = head + 6;
  while (bytes[start] === 13 || bytes[start] === 10) start++;
  const end = raw.indexOf("endstream", start);
  if (end < 0 || end > to + 64) return null;

  let stop = end;
  while (stop > start && (bytes[stop - 1] === 10 || bytes[stop - 1] === 13)) stop--;
  const slice = bytes.subarray(start, stop);
  if (!slice.length) return null;

  for (const fmt of ["deflate", "deflate-raw"]) {
    try { return await inflate(slice, fmt); } catch { /* άλλο filter */ }
  }
  return slice;                                   // ασυμπίεστο
}

async function pdfText(bytes) {
  const raw = latin.decode(bytes);

  // 1. Ευρετήριο αντικειμένων
  const objects = new Map();
  for (const m of raw.matchAll(/(\d+)\s+0\s+obj\b/g)) {
    const start = m.index + m[0].length;
    const end = raw.indexOf("endobj", start);
    if (end > 0) objects.set(Number(m[1]), { start, end });
  }

  // 2. CMaps ανά αντικείμενο-γραμματοσειράς
  const cmapCache = new Map();
  const cmapFor = async (fontObjNum) => {
    if (cmapCache.has(fontObjNum)) return cmapCache.get(fontObjNum);
    let map = null;
    const font = objects.get(fontObjNum);
    if (font) {
      const decl = raw.slice(font.start, font.end);
      const ref = /\/ToUnicode\s+(\d+)\s+0\s+R/.exec(decl);
      const target = ref && objects.get(Number(ref[1]));
      if (target) {
        const data = await objectStream(bytes, raw, target.start, target.end);
        if (data) map = parseCMap(latin.decode(data));
      }
    }
    cmapCache.set(fontObjNum, map);
    return map;
  };

  // 3. Όνομα πόρου (/F1) → αντικείμενο γραμματοσειράς, από κάθε /Font << … >>
  const fontByName = new Map();
  for (const block of raw.matchAll(/\/Font\s*<<([\s\S]{0,4000}?)>>/g)) {
    for (const e of block[1].matchAll(/\/([A-Za-z0-9_.#-]+)\s+(\d+)\s+0\s+R/g)) {
      fontByName.set(e[1], Number(e[2]));
    }
  }

  // 4. Τα content streams, με ενεργή γραμματοσειρά ανά σημείο
  const decodeWithMap = (codes, map) => {
    let out = "";
    for (let i = 0; i + 1 < codes.length; i += 2) {
      const code = (codes.charCodeAt(i) << 8) | codes.charCodeAt(i + 1);
      out += map.get(code) ?? "";
    }
    return out;
  };
  const unescapeLiteral = (s) => s
    .replace(/\\([()\\])/g, "$1")
    .replace(/\\n/g, "\n").replace(/\\r/g, "").replace(/\\t/g, " ")
    .replace(/\\(\d{1,3})/g, (_, o) => String.fromCharCode(parseInt(o, 8)));

  const chunks = [];
  // Τα Tm/Td δεν σημαίνουν πάντα νέα γραμμή — ο Chrome τα χρησιμοποιεί και για
  // μετακίνηση μέσα στην ίδια γραμμή. Κοιτάμε αν άλλαξε το Y.
  const TOKEN = new RegExp([
    /\/([A-Za-z0-9_.#-]+)\s+[\d.]+\s+Tf/,          // 1: επιλογή γραμματοσειράς
    /<([0-9A-Fa-f\s]+)>/,                          // 2: hex string
    /\((?:\\.|[^\\()])*\)/,                        // literal string
    /((?:-?[\d.]+\s+){6})Tm/,                      // 3: text matrix
    /((?:-?[\d.]+\s+){2})T[dD]/,                   // 4: text displacement
    /T\*|ET|BT/,
  ].map((r) => r.source).join("|"), "g");

  for (const [, span] of objects) {
    const decl = raw.slice(span.start, Math.min(span.end, span.start + 400));
    if (/\/(Image|Font|FontFile|ToUnicode|XObject\s*<<)/.test(decl) && !/\/Contents/.test(decl)) {
      if (!/\/Length/.test(decl) || /\/Subtype\s*\/Image/.test(decl)) continue;
    }
    const data = await objectStream(bytes, raw, span.start, span.end);
    if (!data) continue;
    const text = latin.decode(data);
    if (!/\bTj\b|\bTJ\b|\bTf\b/.test(text)) continue;

    let map = null;
    let lastY = null, lastX = null;

    // Τα κενά είναι κανονικά glyphs μέσα στο κείμενο· το Td μετακινεί απλώς τον
    // κέρσορα ανά γράμμα. Νέα γραμμή μόνο όταν αλλάζει το Y.
    const moved = (x, y) => {
      if (lastY !== null && Math.abs(y - lastY) > 2) chunks.push("\n");
      lastY = y; lastX = x;
    };

    for (const g of text.matchAll(TOKEN)) {
      const token = g[0];
      if (g[1] !== undefined) {                    // /F1 12 Tf
        map = await cmapFor(fontByName.get(g[1]));
        continue;
      }
      if (g[3] !== undefined) {                    // a b c d e f Tm
        const n = g[3].trim().split(/\s+/).map(Number);
        moved(n[4], n[5]);
        continue;
      }
      if (g[4] !== undefined) {                    // tx ty Td
        const n = g[4].trim().split(/\s+/).map(Number);
        moved((lastX ?? 0) + n[0], (lastY ?? 0) + n[1]);
        continue;
      }
      if (g[2] !== undefined) {                    // <00030004> hex string
        const hex = g[2].replace(/\s+/g, "");
        if (map) {
          // Με CMap: 4 hex ψηφία = ένας κωδικός glyph, απευθείας στον χάρτη.
          let out = "";
          for (let i = 0; i + 3 < hex.length; i += 4) out += map.get(parseInt(hex.slice(i, i + 4), 16)) ?? "";
          chunks.push(out);
        } else {
          // Χωρίς CMap: 2 hex ψηφία = ένας χαρακτήρας.
          let out = "";
          for (let i = 0; i + 1 < hex.length; i += 2) out += String.fromCharCode(parseInt(hex.slice(i, i + 2), 16));
          chunks.push(out);
        }
        continue;
      }
      if (token[0] === "(") {                      // (literal)
        const body = unescapeLiteral(token.slice(1, -1));
        chunks.push(map ? decodeWithMap(body, map) : body);
        continue;
      }
      if (token === "T*") { chunks.push("\n"); lastY = null; }
      else if (token === "ET" || token === "BT") { lastX = null; }
    }
    if (chunks.length > 60000) break;
  }

  return chunks.join("")
    // Τα PDF γράφουν «ﬁ» ως ένα glyph — χωρίς κανονικοποίηση, το «ﬁntech»
    // δεν ταιριάζει ποτέ με αναζήτηση για «fintech».
    .normalize("NFKC")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/\n[ \t]+/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/* ── DOCX (zip → word/document.xml) ───────────────────────── */
async function docxText(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const SIG = 0x04034b50;

  for (let i = 0; i < bytes.length - 4; i++) {
    if (view.getUint32(i, true) !== SIG) continue;
    const method = view.getUint16(i + 8, true);
    const compSize = view.getUint32(i + 18, true);
    const nameLen = view.getUint16(i + 26, true);
    const extraLen = view.getUint16(i + 28, true);
    const nameStart = i + 30;
    const name = dec.decode(bytes.subarray(nameStart, nameStart + nameLen));
    if (name !== "word/document.xml") continue;

    const dataStart = nameStart + nameLen + extraLen;
    const data = bytes.subarray(dataStart, dataStart + (compSize || bytes.length - dataStart));
    const xmlBytes = method === 0 ? data : await inflate(data, "deflate-raw");
    const xml = dec.decode(xmlBytes);
    return xml
      .replace(/<\/w:p>/g, "\n")
      .replace(/<w:tab[^>]*\/>/g, " ")
      .replace(/<[^>]+>/g, "")
      .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
      .replace(/[ \t]{2,}/g, " ").replace(/\n{3,}/g, "\n\n").trim();
  }
  return "";
}

const toBase64 = (bytes) => {
  let bin = "";
  const step = 0x8000;
  for (let i = 0; i < bytes.length; i += step) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + step));
  }
  return btoa(bin);
};

/** Διαβάζει το αρχείο που ανέβασε ο χρήστης. */
export async function readCV(file) {
  if (file.size > MAX_CV_BYTES) throw new Error("File is larger than 8 MB");

  const bytes = new Uint8Array(await file.arrayBuffer());
  const ext = (file.name.split(".").pop() || "").toLowerCase();

  let text = "";
  try {
    if (ext === "pdf") text = await pdfText(bytes);
    else if (ext === "docx") text = await docxText(bytes);
    else text = dec.decode(bytes);
  } catch (e) {
    text = "";
  }

  return {
    filename: file.name,
    mime: file.type || (ext === "pdf" ? "application/pdf" : "application/octet-stream"),
    base64: toBase64(bytes),
    text: text.slice(0, 20000),
    size: file.size,
    addedAt: new Date().toISOString(),
  };
}

/* ── Τι μπορούμε να μαντέψουμε από το κείμενο ─────────────── */
const EMAIL_RE = /[\w.+-]+@[\w-]+\.[\w.-]*[\w]/;
const PHONE_RE = /(\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3}[\s.-]?\d{3,4}/;
const LINKEDIN_RE = /(?:https?:\/\/)?(?:[a-z]{2,3}\.)?linkedin\.com\/in\/[\w\-%]+/i;
const GITHUB_RE = /(?:https?:\/\/)?(?:www\.)?github\.com\/[\w\-]+/i;


/** Μαντεύει στοιχεία επικοινωνίας + πιθανούς τίτλους από το κείμενο του CV. */
// Το ίδιο λεξιλόγιο με τις προτάσεις: ό,τι μπορεί να προταθεί μπορεί και να
// αναγνωριστεί μέσα στο βιογραφικό.
const COMMON_TITLES = ALL_PROFESSIONS;

export function guessFromCV(text) {
  const out = { name: "", email: "", phone: "", linkedin: "", github: "", titles: [] };
  if (!text) return out;

  out.email = (text.match(EMAIL_RE) || [""])[0];
  const phone = text.match(PHONE_RE);
  if (phone && phone[0].replace(/\D/g, "").length >= 9) out.phone = phone[0].trim();
  out.linkedin = (text.match(LINKEDIN_RE) || [""])[0];
  out.github = (text.match(GITHUB_RE) || [""])[0];

  // Το όνομα είναι σχεδόν πάντα η πρώτη «καθαρή» γραμμή του CV.
  for (const raw of text.split(/\n/).slice(0, 12)) {
    const line = raw.replace(/^[#*\s]+/, "").trim();
    if (line.length < 4 || line.length > 45) continue;
    if (/[@\d]|http|curriculum|resume|\bcv\b/i.test(line)) continue;
    const words = line.split(/\s+/);
    if (words.length >= 2 && words.length <= 4) { out.name = line; break; }
  }

  const low = text.toLowerCase();
  const scored = COMMON_TITLES
    .map((t) => ({ t, n: (low.match(new RegExp(t.toLowerCase(), "g")) || []).length }))
    .filter((x) => x.n > 0)
    .sort((a, b) => b.n - a.n);
  out.titles = scored.slice(0, 5).map((x) => x.t);

  return out;
}

export { COMMON_TITLES };
