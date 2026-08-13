"use client";

import { FileText, Inbox, MessagesSquare, Plus } from "lucide-react";
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

function EmptyState({
  icon: Icon,
  message,
}: {
  icon: typeof Inbox;
  message: string;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-3 py-6 text-center text-sm text-muted-foreground">
        <div className="flex size-10 items-center justify-center rounded-full bg-muted">
          <Icon className="size-5" />
        </div>
        {message}
      </CardContent>
    </Card>
  );
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
      <div className="animate-fade-in-up mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <Button asChild>
          <Link href="/resume/new">
            <Plus className="size-4" />
            Upload resume
          </Link>
        </Button>
      </div>

      {error && <p className="mb-6 text-sm text-destructive">{error}</p>}

      <section className="mb-10">
        <h2 className="mb-3 flex items-center gap-2 text-lg font-medium">
          <FileText className="size-4 text-muted-foreground" />
          Your resumes
        </h2>
        {resumes === null ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : resumes.length === 0 ? (
          <EmptyState
            icon={Inbox}
            message="No resumes yet. Upload one to get a role-aligned ATS analysis and start a mock interview."
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {resumes.map((resume, index) => (
              <Link key={resume.id} href={`/resume/${resume.id}`}>
                <Card
                  className="animate-fade-in-up h-full transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
                  style={{ animationDelay: `${index * 0.05}s` }}
                >
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
        <h2 className="mb-3 flex items-center gap-2 text-lg font-medium">
          <MessagesSquare className="size-4 text-muted-foreground" />
          Interview sessions
        </h2>
        {sessions === null ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : sessions.length === 0 ? (
          <EmptyState
            icon={MessagesSquare}
            message="No mock interviews yet. Start one from a resume's page."
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {sessions.map((session, index) => (
              <Link key={session.id} href={`/interview/${session.id}`}>
                <Card
                  className="animate-fade-in-up h-full transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
                  style={{ animationDelay: `${index * 0.05}s` }}
                >
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
