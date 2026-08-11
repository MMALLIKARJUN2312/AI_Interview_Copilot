"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

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
    <div className="mx-auto flex max-w-3xl flex-1 flex-col items-center justify-center gap-6 px-4 py-24 text-center">
      <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
        Prep for the role you actually applied for.
      </h1>
      <p className="max-w-xl text-balance text-muted-foreground">
        Upload your resume for a specific job role and get an ATS analysis,
        then take an AI mock interview built entirely from that resume and
        role &mdash; not generic questions.
      </p>
      <div className="flex gap-3">
        <Button size="lg" asChild>
          <Link href="/register">Get started</Link>
        </Button>
        <Button size="lg" variant="outline" asChild>
          <Link href="/login">Log in</Link>
        </Button>
      </div>
    </div>
  );
}
