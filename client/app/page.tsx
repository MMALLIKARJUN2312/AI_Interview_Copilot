"use client";

import { Compass, MessagesSquare, ScanSearch, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

const FEATURES = [
  {
    icon: ScanSearch,
    title: "Role-aligned ATS analysis",
    description:
      "Upload your resume for the exact role you're targeting and get a score, strengths, and gaps scored against that role — not a generic template.",
  },
  {
    icon: MessagesSquare,
    title: "Real mock interviews",
    description:
      "Questions are generated from your actual resume and role, then each answer gets scored with concrete, specific feedback.",
  },
  {
    icon: Compass,
    title: "A roadmap to close the gap",
    description:
      "Walk away with a prioritized learning plan built from your interview performance, not a one-size-fits-all checklist.",
  },
];

export default function HomePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [isLoading, user, router]);

  if (isLoading || user) {
    return null;
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-center px-4 py-20 sm:py-28">
      <div className="animate-fade-in-up glass mb-8 inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-medium text-muted-foreground">
        <Sparkles className="size-3.5 text-[var(--brand-via)]" />
        AI-powered interview preparation
      </div>

      <h1
        className="animate-fade-in-up max-w-3xl text-balance text-center text-4xl font-semibold tracking-tight sm:text-6xl"
        style={{ animationDelay: "0.05s" }}
      >
        Prep for{" "}
        <span className="text-gradient-brand">the role you actually applied for</span>.
      </h1>

      <p
        className="animate-fade-in-up mt-6 max-w-xl text-balance text-center text-muted-foreground sm:text-lg"
        style={{ animationDelay: "0.12s" }}
      >
        Upload your resume for a specific job role and get an ATS analysis, then
        take an AI mock interview built entirely from that resume and role
        &mdash; not generic questions.
      </p>

      <div
        className="animate-fade-in-up mt-9 flex flex-col gap-3 sm:flex-row"
        style={{ animationDelay: "0.18s" }}
      >
        <Button size="lg" asChild>
          <Link href="/register">Get started free</Link>
        </Button>
        <Button size="lg" variant="outline" asChild>
          <Link href="/login">Log in</Link>
        </Button>
      </div>

      <div className="mt-24 grid w-full gap-5 sm:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, description }, index) => (
          <Card
            key={title}
            className="animate-fade-in-up transition-transform duration-300 hover:-translate-y-1"
            style={{ animationDelay: `${0.24 + index * 0.08}s` }}
          >
            <CardHeader>
              <div className="mb-2 flex size-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,var(--brand-from),var(--brand-to))] text-primary-foreground shadow-sm">
                <Icon className="size-5" />
              </div>
              <CardTitle className="text-base">{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}
