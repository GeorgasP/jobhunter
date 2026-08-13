/**
 * Landing page — public marketing.
 * Sections: Hero · Social proof · Features · Pricing · FAQ · CTA
 */
import Link from "next/link";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import { Sparkles, Zap, Target, FileText, Check } from "lucide-react";

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <Nav />
      <Hero />
      <Features />
      <Pricing />
      <FAQ />
      <Footer />
    </main>
  );
}

function Nav() {
  return (
    <header className="border-b sticky top-0 bg-background/80 backdrop-blur z-50">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl">
          <Sparkles className="w-5 h-5 text-primary" />
          JobHunter
        </Link>
        <nav className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
          <a href="#features" className="hover:text-foreground">Features</a>
          <a href="#pricing" className="hover:text-foreground">Pricing</a>
          <a href="#faq" className="hover:text-foreground">FAQ</a>
        </nav>
        <div className="flex items-center gap-3">
          <SignedOut>
            <SignInButton mode="modal">
              <button className="text-sm font-medium hover:text-foreground">Sign in</button>
            </SignInButton>
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Get started
            </Link>
          </SignedOut>
          <SignedIn>
            <Link
              href="/dashboard"
              className="text-sm font-medium hover:text-foreground"
            >
              Dashboard
            </Link>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="container mx-auto px-4 py-20 md:py-32 text-center">
      <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 text-xs font-medium bg-secondary rounded-full">
        <Sparkles className="w-3 h-3" />
        AI-powered. Built for job seekers in 2026.
      </div>
      <h1 className="text-4xl md:text-7xl font-bold tracking-tight mb-6">
        Stop wasting your life
        <br />
        <span className="text-primary">on job applications.</span>
      </h1>
      <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
        Upload your CV. We scout 100+ companies daily, write personalized cover letters
        with AI, and pre-fill applications. You just show up to the interview.
      </p>
      <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
        <Link
          href="/dashboard"
          className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-8 py-4 text-base font-medium text-primary-foreground hover:bg-primary/90"
        >
          Get started free
          <Zap className="w-4 h-4" />
        </Link>
        <a
          href="#features"
          className="inline-flex items-center justify-center px-8 py-4 text-base font-medium border rounded-md hover:bg-secondary"
        >
          See how it works
        </a>
      </div>
      <p className="text-sm text-muted-foreground">
        Free tier · No credit card · 10 matches/day
      </p>
    </section>
  );
}

function Features() {
  const features = [
    {
      icon: Target,
      title: "Daily personalized matches",
      desc: "100+ company career pages scanned every day. Filtered to your preferences, ranked by relevance.",
    },
    {
      icon: FileText,
      title: "AI-written cover letters",
      desc: "Claude generates a unique cover letter for every match, tailored to the company and role.",
    },
    {
      icon: Zap,
      title: "One-click apply",
      desc: "Pre-filled forms for Greenhouse, Lever, Workable. You review, you approve, done.",
    },
  ];
  return (
    <section id="features" className="container mx-auto px-4 py-20 border-t">
      <h2 className="text-3xl md:text-5xl font-bold text-center mb-4">
        How it works
      </h2>
      <p className="text-center text-muted-foreground mb-16 max-w-2xl mx-auto">
        Three steps. Five minutes a day. Tens of applications without burning out.
      </p>
      <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        {features.map((f, i) => (
          <div key={i} className="text-center">
            <div className="inline-flex w-12 h-12 items-center justify-center rounded-lg bg-primary/10 text-primary mb-4">
              <f.icon className="w-6 h-6" />
            </div>
            <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
            <p className="text-muted-foreground text-sm">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Pricing() {
  const tiers = [
    {
      name: "Free",
      price: "€0",
      period: "forever",
      features: [
        "10 daily job matches",
        "Manual cover letter templates",
        "Basic application tracking",
        "Email notifications",
      ],
      cta: "Start free",
      highlight: false,
    },
    {
      name: "Pro",
      price: "€19",
      period: "/month",
      features: [
        "50 daily job matches",
        "5 AI cover letters/day",
        "Multi-language support (5 languages)",
        "Application tracking dashboard",
        "Email + Telegram notifications",
        "Cancel anytime",
      ],
      cta: "Start Pro",
      highlight: true,
    },
    {
      name: "Premium",
      price: "€49",
      period: "/month",
      features: [
        "Unlimited daily matches",
        "Unlimited AI cover letters",
        "One-click apply (Greenhouse/Lever)",
        "AI interview prep assistant",
        "Analytics dashboard",
        "Priority support",
      ],
      cta: "Go Premium",
      highlight: false,
    },
  ];
  return (
    <section id="pricing" className="container mx-auto px-4 py-20 border-t">
      <h2 className="text-3xl md:text-5xl font-bold text-center mb-4">
        Simple pricing
      </h2>
      <p className="text-center text-muted-foreground mb-16">
        Start free. Upgrade when you're getting interviews.
      </p>
      <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {tiers.map((tier, i) => (
          <div
            key={i}
            className={`rounded-2xl border p-8 ${
              tier.highlight
                ? "border-primary shadow-xl scale-105 bg-primary/5"
                : ""
            }`}
          >
            {tier.highlight && (
              <div className="inline-block px-2 py-1 mb-4 text-xs font-medium bg-primary text-primary-foreground rounded">
                Most popular
              </div>
            )}
            <h3 className="font-bold text-xl mb-2">{tier.name}</h3>
            <div className="mb-6">
              <span className="text-4xl font-bold">{tier.price}</span>
              <span className="text-muted-foreground">{tier.period}</span>
            </div>
            <ul className="space-y-3 mb-8 text-sm">
              {tier.features.map((f, j) => (
                <li key={j} className="flex items-start gap-2">
                  <Check className="w-4 h-4 mt-0.5 text-primary shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            <Link
              href="/dashboard"
              className={`block w-full text-center rounded-md py-3 font-medium ${
                tier.highlight
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "border hover:bg-secondary"
              }`}
            >
              {tier.cta}
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
}

function FAQ() {
  const items = [
    {
      q: "Is auto-applying legal?",
      a: "We use official ATS APIs (Greenhouse, Lever, Workable) that explicitly support programmatic applications. We never scrape LinkedIn or violate any platform's Terms of Service.",
    },
    {
      q: "How are AI cover letters different from templates?",
      a: "Each letter is generated by Claude (Anthropic) using your full CV plus the specific job description. The result references actual experience from your CV and addresses the company by name. No two letters are alike.",
    },
    {
      q: "What if the AI gets the cover letter wrong?",
      a: "You always review before applying. The dashboard lets you edit, regenerate, or replace any letter before submission.",
    },
    {
      q: "Can I cancel anytime?",
      a: "Yes. Pro and Premium are month-to-month. Cancel via the billing portal anytime. You keep access until end of billing period.",
    },
    {
      q: "Which companies are scanned?",
      a: "We track 100+ companies across crypto/fintech, tech startups, EU SaaS, prop firms, and more. New companies added weekly based on user demand. Specific list at /companies.",
    },
  ];
  return (
    <section id="faq" className="container mx-auto px-4 py-20 border-t">
      <h2 className="text-3xl md:text-5xl font-bold text-center mb-16">
        Frequently asked
      </h2>
      <div className="max-w-3xl mx-auto space-y-6">
        {items.map((item, i) => (
          <div key={i} className="border-b pb-6">
            <h3 className="font-semibold mb-2">{item.q}</h3>
            <p className="text-muted-foreground">{item.a}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t py-12 mt-20">
      <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
        <p>© 2026 JobHunter. Built with AI, for humans.</p>
      </div>
    </footer>
  );
}
