/*
 * Επαγγέλματα ανά κλάδο.
 *
 * Το λεξιλόγιο των προτάσεων έβγαινε μέχρι τώρα από τις αγγελίες που είχαν
 * κατέβει, με μια μικρή λίστα σπόρων για την πρώτη φορά. Η λίστα όμως ήταν
 * γραφείου: στην υγεία είχε τέσσερις τίτλους και κανέναν φυσικοθεραπευτή.
 * Αν το επάγγελμά σου δεν προτείνεται πουθενά, ο κλάδος στις ρυθμίσεις δεν
 * σου χρησιμεύει σε τίποτα.
 *
 * Οι τίτλοι είναι στα αγγλικά επειδή έτσι γράφονται στις αγγελίες. Η
 * αναζήτηση ανέχεται τυπογραφικά, οπότε δεν χρειάζεται να τους ξέρει κανείς
 * απ' έξω.
 */

export const BY_INDUSTRY = {
  health: [
    "Registered Nurse", "Staff Nurse", "Nurse Practitioner", "Mental Health Nurse",
    "Theatre Nurse", "ICU Nurse", "Midwife", "Healthcare Assistant", "Care Assistant",
    "Support Worker", "Care Home Manager", "Physiotherapist", "Occupational Therapist",
    "Speech and Language Therapist", "Radiographer", "Sonographer", "Paramedic",
    "Physician", "General Practitioner", "Surgeon", "Anaesthetist", "Psychiatrist",
    "Psychologist", "Psychotherapist", "Counsellor", "Dentist", "Dental Nurse",
    "Dental Hygienist", "Optometrist", "Optician", "Pharmacist", "Pharmacy Technician",
    "Dietitian", "Nutritionist", "Podiatrist", "Chiropractor", "Osteopath",
    "Phlebotomist", "Medical Laboratory Technician", "Biomedical Scientist",
    "Medical Secretary", "Clinical Research Associate", "Veterinarian",
    "Veterinary Nurse", "Medical Assistant", "Health and Safety Officer",
  ],
  education: [
    "Teacher", "Primary School Teacher", "Secondary School Teacher", "Teaching Assistant",
    "Special Educational Needs Teacher", "Nursery Practitioner", "Early Years Educator",
    "Lecturer", "Professor", "Language Teacher", "English Teacher", "Tutor",
    "Instructor", "Training Specialist", "Learning and Development Manager",
    "Curriculum Designer", "Instructional Designer", "School Counsellor",
    "Academic Advisor", "Librarian", "Education Coordinator", "Driving Instructor",
  ],
  manufacturing: [
    "Production Operative", "Machine Operator", "CNC Machinist", "Welder", "Fabricator",
    "Assembler", "Maintenance Technician", "Maintenance Engineer", "Mechanical Engineer",
    "Electrical Engineer", "Manufacturing Engineer", "Process Engineer",
    "Quality Inspector", "Quality Engineer", "Production Manager", "Plant Manager",
    "Shift Supervisor", "Toolmaker", "Industrial Electrician", "Health and Safety Advisor",
  ],
  automotive: [
    "Vehicle Technician", "Mechanic", "HGV Mechanic", "Auto Electrician",
    "Panel Beater", "Vehicle Painter", "MOT Tester", "Service Advisor",
    "Parts Advisor", "Automotive Engineer", "Workshop Manager", "Car Sales Executive",
  ],
  transport: [
    "Driver", "Delivery Driver", "HGV Driver", "Lorry Driver", "Van Driver",
    "Bus Driver", "Train Driver", "Taxi Driver", "Courier", "Chauffeur",
    "Forklift Driver", "Pilot", "Cabin Crew", "Air Traffic Controller",
    "Ship Captain", "Deckhand", "Transport Manager", "Fleet Manager",
  ],
  logistics: [
    "Warehouse Operative", "Warehouse Manager", "Picker Packer", "Stock Controller",
    "Inventory Manager", "Logistics Coordinator", "Supply Chain Manager",
    "Supply Chain Analyst", "Freight Forwarder", "Customs Broker",
    "Procurement Manager", "Buyer", "Dispatcher", "Operations Manager",
  ],
  hospitality: [
    "Chef", "Head Chef", "Sous Chef", "Commis Chef", "Pastry Chef", "Cook",
    "Kitchen Porter", "Waiter", "Waitress", "Bartender", "Barista", "Sommelier",
    "Restaurant Manager", "Hotel Manager", "Front Office Manager", "Receptionist",
    "Concierge", "Housekeeper", "Housekeeping Supervisor", "Event Coordinator",
    "Banqueting Manager", "Food and Beverage Manager",
  ],
  food: [
    "Food Production Operative", "Butcher", "Baker", "Food Technologist",
    "Quality Assurance Technician", "Food Safety Manager", "Nutrition Advisor",
  ],
  retail: [
    "Sales Assistant", "Shop Assistant", "Cashier", "Store Manager",
    "Assistant Store Manager", "Visual Merchandiser", "Merchandiser",
    "Category Manager", "Buyer", "Stock Assistant", "Retail Supervisor",
    "Customer Advisor", "E-commerce Manager",
  ],
  travel: [
    "Travel Consultant", "Travel Agent", "Tour Guide", "Tour Operator",
    "Reservations Agent", "Cruise Staff", "Resort Manager", "Destination Manager",
  ],
  realestate: [
    "Estate Agent", "Letting Agent", "Property Manager", "Facilities Manager",
    "Surveyor", "Quantity Surveyor", "Valuer", "Architect", "Site Manager",
    "Construction Manager", "Civil Engineer", "Structural Engineer",
    "Electrician", "Plumber", "Carpenter", "Bricklayer", "Painter and Decorator",
    "Plasterer", "Roofer", "Scaffolder", "HVAC Technician", "Building Surveyor",
  ],
  fitness: [
    "Personal Trainer", "Fitness Instructor", "Gym Manager", "Yoga Teacher",
    "Pilates Instructor", "Swimming Instructor", "Sports Coach", "Sports Therapist",
    "Strength and Conditioning Coach", "Lifeguard",
  ],
  nonprofit: [
    "Fundraising Manager", "Grants Manager", "Programme Manager", "Project Officer",
    "Volunteer Coordinator", "Community Outreach Worker", "Social Worker",
    "Caseworker", "Advocacy Officer", "Policy Officer", "Monitoring and Evaluation Officer",
  ],
  public: [
    "Civil Servant", "Policy Advisor", "Administrative Officer", "Case Officer",
    "Planning Officer", "Environmental Health Officer", "Social Worker",
    "Police Officer", "Firefighter", "Prison Officer", "Immigration Officer",
    "Tax Inspector", "Public Health Officer",
  ],
  hr: [
    "Recruiter", "Talent Acquisition Specialist", "HR Manager", "HR Business Partner",
    "HR Administrator", "People Operations Manager", "Payroll Specialist",
    "Compensation and Benefits Manager", "Learning and Development Specialist",
    "Employee Relations Advisor", "Office Manager", "Executive Assistant",
    "Personal Assistant", "Administrative Assistant", "Virtual Assistant",
  ],
  banking: [
    "Bank Teller", "Personal Banker", "Relationship Manager", "Credit Analyst",
    "Loan Officer", "Mortgage Advisor", "Underwriter", "Compliance Officer",
    "Risk Analyst", "Anti-Money Laundering Analyst", "Financial Advisor",
    "Investment Analyst", "Wealth Manager", "Insurance Broker", "Claims Handler",
    "Actuary", "Accountant", "Management Accountant", "Auditor", "Bookkeeper",
    "Financial Controller", "Financial Analyst", "Tax Advisor",
  ],
  fintech: [
    "Product Manager", "Compliance Manager", "Risk Manager", "Payments Specialist",
    "Fraud Analyst", "Onboarding Specialist", "Partnerships Manager",
  ],
  trading: [
    "Trader", "Quantitative Analyst", "Quantitative Developer", "Portfolio Manager",
    "Execution Trader", "Market Analyst", "Broker",
  ],
  crypto: [
    "Blockchain Developer", "Smart Contract Engineer", "Crypto Analyst",
    "Community Manager", "Compliance Analyst",
  ],
  betting: [
    "Odds Compiler", "Trading Analyst", "Customer Support Agent",
    "Responsible Gambling Officer", "Sportsbook Manager",
  ],
  tech: [
    "Software Engineer", "Frontend Engineer", "Backend Engineer", "Full Stack Engineer",
    "Mobile Developer", "iOS Developer", "Android Developer", "DevOps Engineer",
    "Site Reliability Engineer", "Cloud Engineer", "Platform Engineer",
    "Security Engineer", "Network Engineer", "Systems Administrator",
    "IT Support Specialist", "Helpdesk Technician", "Solutions Architect",
    "Engineering Manager", "QA Engineer", "Test Automation Engineer",
    "Technical Writer", "Scrum Master",
  ],
  data: [
    "Data Analyst", "Data Scientist", "Data Engineer", "Analytics Engineer",
    "Business Intelligence Analyst", "Database Administrator", "Business Analyst",
    "Research Analyst", "Statistician",
  ],
  ai: [
    "Machine Learning Engineer", "AI Engineer", "Research Scientist",
    "Data Scientist", "MLOps Engineer", "Prompt Engineer", "Computer Vision Engineer",
  ],
  saas: [
    "Customer Success Manager", "Implementation Consultant", "Solutions Engineer",
    "Sales Engineer", "Renewals Manager", "Onboarding Specialist",
  ],
  design: [
    "Graphic Designer", "Product Designer", "UX Designer", "UI Designer",
    "UX Researcher", "Motion Designer", "Illustrator", "Art Director",
    "Interior Designer", "Fashion Designer", "Industrial Designer",
  ],
  marketing: [
    "Marketing Manager", "Digital Marketing Manager", "Content Writer", "Copywriter",
    "SEO Specialist", "PPC Specialist", "Social Media Manager", "Brand Manager",
    "Growth Marketer", "Email Marketing Specialist", "Marketing Analyst",
    "Public Relations Manager", "Communications Manager", "Event Manager",
  ],
  media: [
    "Journalist", "Editor", "Copy Editor", "Video Editor", "Videographer",
    "Photographer", "Producer", "Podcast Producer", "Broadcast Engineer",
    "Translator", "Interpreter", "Content Manager", "Community Manager",
  ],
  gaming: [
    "Game Developer", "Game Designer", "Level Designer", "3D Artist",
    "Animator", "Technical Artist", "QA Tester", "Game Producer",
  ],
  mobility: [
    "Operations Manager", "City Manager", "Fleet Operations Specialist",
    "Driver Supply Manager", "Field Operations Coordinator",
  ],
  consumer: [
    "Brand Manager", "Product Manager", "Category Manager", "Customer Insights Analyst",
    "Packaging Designer", "Trade Marketing Manager",
  ],
};

/* Γενικοί ρόλοι που υπάρχουν σχεδόν παντού και δεν ανήκουν σε έναν κλάδο. */
export const CROSS_INDUSTRY = [
  "Customer Success Manager", "Customer Support Specialist",
  "Customer Service Representative", "Account Manager", "Account Executive",
  "Business Development Representative", "Sales Manager", "Sales Representative",
  "Project Manager", "Programme Manager", "Operations Manager", "Team Leader",
  "Consultant", "Analyst", "Coordinator", "Receptionist", "Cleaner",
  "Security Officer", "Warehouse Operative", "Technician",
];

/** Όλα τα επαγγέλματα, χωρίς διπλά, με σταθερή σειρά. */
export const ALL_PROFESSIONS = [...new Set(
  [...CROSS_INDUSTRY, ...Object.values(BY_INDUSTRY).flat()]
)];

/** Τα επαγγέλματα των κλάδων που διάλεξε ο χρήστης — μπαίνουν πρώτα. */
export function professionsFor(industries = []) {
  const wanted = industries.map((i) => String(i).toLowerCase());
  const picked = wanted.flatMap((i) => BY_INDUSTRY[i] || []);
  return [...new Set([...picked, ...CROSS_INDUSTRY])];
}
