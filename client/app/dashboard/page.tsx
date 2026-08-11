"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/protected-route";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api } from "@/lib/api";
import type { ResumeSummary, SessionSummary } from "@/lib/types";

function statusVariant(
  status: string,
): "success" | "destructive" | "secondary" {
  if (status === "analyzed" || status === "completed") return "success";
  if (status === "failed" || status === "abandoned") return "destructive";
  return "secondary";
}

function DashboardContent() {
  const [resumes, setResumes] = useState<ResumeSummary[] | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listResumes(), api.listSessions()])
      .then(([resumeList, sessionList]) => {
        setResumes(resumeList);
        setSessions(sessionList);
      })
      .catch(() => setError("Unable to load your dashboard right now."));
  }, []);

  return (
    <div className="mx-auto w-full max-w-4xl flex-1 px-4 py-10">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <Button asChild>
          <Link href="/resume/new">Upload resume</Link>
        </Button>
      </div>

      {error && <p className="mb-6 text-sm text-destructive">{error}</p>}

      <section className="mb-10">
        <h2 className="mb-3 text-lg font-medium">Your resumes</h2>
        {resumes === null ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : resumes.length === 0 ? (
          <Card>
            <CardContent className="text-sm text-muted-foreground">
              No resumes yet. Upload one to get a role-aligned ATS analysis
              and start a mock interview.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {resumes.map((resume) => (
              <Link key={resume.id} href={`/resume/${resume.id}`}>
                <Card className="h-full transition-colors hover:border-foreground/30">
                  <CardHeader>
                    <div className="flex items-center justify-between gap-2">
                      <CardTitle className="text-base">
                        {resume.target_role}
                      </CardTitle>
                      <Badge variant={statusVariant(resume.status)}>
                        {resume.status}
                      </Badge>
                    </div>
                    <CardDescription>
                      {resume.original_filename}
                    </CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-medium">Interview sessions</h2>
        {sessions === null ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : sessions.length === 0 ? (
          <Card>
            <CardContent className="text-sm text-muted-foreground">
              No mock interviews yet. Start one from a resume&apos;s page.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {sessions.map((session) => (
              <Link key={session.id} href={`/interview/${session.id}`}>
                <Card className="h-full transition-colors hover:border-foreground/30">
                  <CardHeader>
                    <div className="flex items-center justify-between gap-2">
                      <CardTitle className="text-base">
                        {session.target_role}
                      </CardTitle>
                      <Badge variant={statusVariant(session.status)}>
                        {session.status}
                      </Badge>
                    </div>
                    <CardDescription>
                      {session.current_index}/{session.total_questions}{" "}
                      answered
                      {session.overall_score !== null &&
                        ` · Score: ${session.overall_score}`}
                    </CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
