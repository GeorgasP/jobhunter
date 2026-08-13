/**
 * Dashboard — main user surface after sign-in.
 * Shows: today's matches, application stats, quick actions.
 */
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import Link from "next/link";
import { ArrowRight, FileText, Briefcase, Send, TrendingUp } from "lucide-react";

export default async function Dashboard() {
  const { userId } = await auth();
  if (!userId) redirect("/");

  // TODO: fetch from backend API
  const stats = {
    todayMatches: 12,
    weekApplications: 8,
    pendingResponses: 3,
    interviewsScheduled: 1,
  };

  return (
    <div className="min-h-screen bg-secondary/30">
      <header className="border-b bg-background">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="font-bold text-xl">JobHunter</Link>
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/dashboard" className="font-medium">Dashboard</Link>
            <Link href="/jobs" className="text-muted-foreground hover:text-foreground">Jobs</Link>
            <Link href="/applications" className="text-muted-foreground hover:text-foreground">Applications</Link>
            <Link href="/settings" className="text-muted-foreground hover:text-foreground">Settings</Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Welcome back 👋</h1>
          <p className="text-muted-foreground">
            Here's your job hunt status today.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          <StatCard
            icon={Briefcase}
            label="Today's matches"
            value={stats.todayMatches}
            href="/jobs"
          />
          <StatCard
            icon={Send}
            label="Applications this week"
            value={stats.weekApplications}
            href="/applications"
          />
          <StatCard
            icon={FileText}
            label="Pending responses"
            value={stats.pendingResponses}
          />
          <StatCard
            icon={TrendingUp}
            label="Interviews scheduled"
            value={stats.interviewsScheduled}
            highlight
          />
        </div>

        <section className="bg-background rounded-2xl border p-8 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">Today's top matches</h2>
            <Link href="/jobs" className="text-sm text-primary hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="text-center py-16 text-muted-foreground">
            <p className="mb-2">No matches yet today.</p>
            <p className="text-sm">
              {"We're scanning. Check back in a few minutes."}
            </p>
          </div>
        </section>

        <section className="bg-background rounded-2xl border p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">Quick start</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            <ActionCard
              title="Upload your CV"
              desc="Required for AI cover letters."
              href="/settings/cvs"
            />
            <ActionCard
              title="Set preferences"
              desc="Locations, salary, role types."
              href="/settings/preferences"
            />
            <ActionCard
              title="Upgrade to Pro"
              desc="50 matches/day + AI letters."
              href="/billing"
              highlight
            />
          </div>
        </section>
      </main>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  href,
  highlight = false,
}: {
  icon: any;
  label: string;
  value: number;
  href?: string;
  highlight?: boolean;
}) {
  const content = (
    <div
      className={`bg-background rounded-2xl border p-6 ${
        highlight ? "border-primary" : ""
      }`}
    >
      <Icon
        className={`w-5 h-5 mb-3 ${
          highlight ? "text-primary" : "text-muted-foreground"
        }`}
      />
      <div className="text-3xl font-bold mb-1">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </div>
  );
  return href ? <Link href={href}>{content}</Link> : content;
}

function ActionCard({
  title,
  desc,
  href,
  highlight = false,
}: {
  title: string;
  desc: string;
  href: string;
  highlight?: boolean;
}) {
  return (
    <Link
      href={href}
      className={`block rounded-xl border p-5 hover:bg-secondary/50 transition ${
        highlight ? "border-primary bg-primary/5" : ""
      }`}
    >
      <h3 className="font-medium mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground">{desc}</p>
    </Link>
  );
}
