import { rankJobs } from "./extension/lib/matcher.js";

// Τυπικοί τίτλοι και περιγραφές όπως εμφανίζονται στην πράξη
const JOBS = [
  { id:"1", title:"Junior Software Engineer", company:"A", location:"Remote", url:"u", description:"1+ years of experience with JavaScript." },
  { id:"2", title:"Software Engineer",        company:"B", location:"Remote", url:"u", description:"You have 2+ years of professional experience." },
  { id:"3", title:"Software Engineer",        company:"C", location:"Remote", url:"u", description:"We need 4 years of experience in backend systems." },
  { id:"4", title:"Senior Software Engineer", company:"D", location:"Remote", url:"u", description:"7+ years of experience required." },
  { id:"5", title:"Software Engineer",        company:"E", location:"Remote", url:"u", description:"Join our team building great products." },
  { id:"6", title:"Engineering Manager",      company:"F", location:"Remote", url:"u", description:"You will lead a team." },
  { id:"7", title:"Director of Engineering",  company:"G", location:"Remote", url:"u", description:"10+ years of experience leading teams." },
  { id:"8", title:"Graduate Software Engineer",company:"H",location:"Remote", url:"u", description:"No experience needed, we train you." },
  { id:"9", title:"Staff Engineer",           company:"I", location:"Remote", url:"u", description:"Deep expertise expected." },
  { id:"10",title:"Software Engineer",        company:"J", location:"Remote", url:"u", description:"Our company was founded 12 years ago. We move fast." },
].map(j => ({ ...j, postedAt: new Date().toISOString() }));

const base = { titles:["Software Engineer"], locations:["Remote"], blockedLocations:[], excludeKeywords:[],
  industries:[], salaryMin:0, salaryCurrency:"EUR", strictLocation:false, remoteOnly:false,
  minScore:0, maxAgeDays:90, languages:["en"] };

for (const lvl of ["entry","mid","senior"]) {
  const res = rankJobs(JOBS, { ...base, experienceLevel: lvl });
  const kept = new Set(res.map(m => m.id));
  console.log(`\n  ── ${lvl.toUpperCase()} ──`);
  for (const j of JOBS) {
    const mark = kept.has(j.id) ? "ΠΕΡΝΑΕΙ" : "  κόπηκε";
    console.log(`   ${mark}  ${j.title.padEnd(28)} ${(j.description.slice(0,34))}`);
  }
  console.log(`   σύνολο: ${res.length}/${JOBS.length}`);
}
