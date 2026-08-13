import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "JobHunter — AI-powered job applications, on autopilot",
  description:
    "Stop spending 100 hours on job applications. JobHunter scouts 100+ companies daily, generates personalized cover letters with AI, and pre-fills applications. You just show up to the interview.",
  openGraph: {
    title: "JobHunter — AI-powered job applications",
    description:
      "Apply to 50 jobs/week in 30 minutes. AI does the grunt work.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en" className={inter.variable}>
        <body className="min-h-screen bg-background font-sans antialiased">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
