"use client";

import { Code2, Laptop2, MessagesSquare } from "lucide-react";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/protected-route";
import { ScoreList } from "@/components/score-list";
import { ScoreRing } from "@/components/score-ring";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ApiError, api } from "@/lib/api";
import type {
  ResumeAnalysisResponse,
  ResumeSummary,
  RoundType,
} from "@/lib/types";

const ROUND_OPTIONS: {
  round_type: RoundType;
  icon: typeof Code2;
  title: string;
  description: string;
  defaultEnabled: boolean;
  defaultCount: number;
}[] = [
  {
    round_type: "dsa_coding",
    icon: Code2,
    title: "DSA coding round",
    description: "Algorithmic problems judged by real input/output test cases.",
    defaultEnabled: true,
    defaultCount: 2,
  },
  {
    round_type: "machine_coding",
    icon: Laptop2,
    title: "Machine coding round",
    description: "Build a small working system, reviewed on design and correctness.",
    defaultEnabled: true,
    defaultCount: 1,
  },
  {
    round_type: "general",
    icon: MessagesSquare,
    title: "General round",
    description: "Behavioral, technical, and system-design questions, answered in writing.",
    defaultEnabled: true,
    defaultCount: 2,
  },
];

function ResumeDetail({ resumeId }: { resumeId: number }) {
  const router = useRouter();
  const [resume, setResume] = useState<ResumeSummary | null>(null);
  const [analysis, setAnalysis] = useState<ResumeAnalysisResponse | null>(
    null,
  );
  const [loadError, setLoadError] = useState<string | null>(null);
  const [roundState, setRoundState] = useState(() =>
    Object.fromEntries(
      ROUND_OPTIONS.map((option) => [
        option.round_type,
        { enabled: option.defaultEnabled, count: option.defaultCount },
      ]),
    ) as Record<RoundType, { enabled: boolean; count: number }>,
  );
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getResume(resumeId)
      .then(setResume)
      .catch(() => setLoadError("Unable to load this resume."));

    api
      .getResumeAnalysis(resumeId)
      .then(setAnalysis)
      .catch((err) => {
        if (!(err instanceof ApiError && err.status === 404)) {
          setLoadError("Unable to load the analysis for this resume.");
        }
      });
  }, [resumeId]);

  async function handleStartInterview() {
    setStartError(null);

    const rounds = ROUND_OPTIONS.filter(
      (option) => roundState[option.round_type].enabled,
    ).map((option) => ({
      round_type: option.round_type,
      num_questions: roundState[option.round_type].count,
    }));

    if (rounds.length === 0) {
      setStartError("Select at least one round to include.");
      return;
    }

    setIsStarting(true);

    try {
      const result = await api.startInterview({ resumeId, rounds });
      router.push(`/interview/${result.session.id}`);
    } catch (err) {
      setStartError(
        err instanceof ApiError
          ? err.message
          : "Could not start the interview. Please try again.",
      );
      setIsStarting(false);
    }
  }

  if (loadError) {
    return (
      <div className="mx-auto w-full max-w-3xl flex-1 px-4 py-10">
        <p className="text-sm text-destructive">{loadError}</p>
      </div>
    );
  }

  if (!resume) {
    return (
      <div className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl flex-1 px-4 py-10">
      <div className="animate-fade-in-up mb-6 flex items-center justify-between gap-2">
        <div>
          <h1 className="font-heading text-2xl font-semibold tracking-tight">
            {resume.target_role}
          </h1>
          <p className="text-sm text-muted-foreground">
            {resume.original_filename}
          </p>
        </div>
        <Badge
          variant={
            resume.status === "analyzed"
              ? "success"
              : resume.status === "failed"
                ? "destructive"
                : "secondary"
          }
        >
          {resume.status}
        </Badge>
      </div>

      {resume.status === "failed" && (
        <Card className="animate-fade-in-up mb-6">
          <CardContent className="text-sm text-destructive">
            Analysis failed for this resume. Please upload it again.
          </CardContent>
        </Card>
      )}

      {analysis && (
        <Card className="animate-fade-in-up mb-6">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle>ATS Score</CardTitle>
                <CardDescription className="mt-1">
                  How well this resume matches a &ldquo;{analysis.target_role}
                  &rdquo; hiring pipeline.
                </CardDescription>
              </div>
              <ScoreRing score={analysis.ats_score} />
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            <ScoreList title="Strengths" items={analysis.strengths} kind="positive" />
            <ScoreList title="Weaknesses" items={analysis.weaknesses} kind="negative" />
            <ScoreList title="Suggestions" items={analysis.suggestions} kind="suggestion" />
          </CardContent>
        </Card>
      )}

      {resume.status === "analyzed" && (
        <Card className="animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
          <CardHeader>
            <div className="mb-1 flex size-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,var(--brand-from),var(--brand-to))] text-primary-foreground shadow-sm">
              <MessagesSquare className="size-5" />
            </div>
            <CardTitle>Start a mock interview</CardTitle>
            <CardDescription>
              A real interview loop, built from this resume and role. Choose which
              rounds to include.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-col gap-3">
              {ROUND_OPTIONS.map((option) => {
                const state = roundState[option.round_type];
                const Icon = option.icon;

                return (
                  <div
                    key={option.round_type}
                    className="flex items-start gap-3 rounded-xl border border-border bg-background/40 p-3"
                  >
                    <input
                      type="checkbox"
                      checked={state.enabled}
                      onChange={(event) =>
                        setRoundState((prev) => ({
                          ...prev,
                          [option.round_type]: { ...prev[option.round_type], enabled: event.target.checked },
                        }))
                      }
                      className="mt-1 size-4 accent-[var(--primary)]"
                      aria-label={`Include ${option.title}`}
                    />
                    <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{option.title}</p>
                      <p className="text-xs text-muted-foreground">{option.description}</p>
                    </div>
                    <Input
                      type="number"
                      min={1}
                      max={5}
                      disabled={!state.enabled}
                      value={state.count}
                      onChange={(event) =>
                        setRoundState((prev) => ({
                          ...prev,
                          [option.round_type]: {
                            ...prev[option.round_type],
                            count: Math.max(1, Math.min(5, Number(event.target.value))),
                          },
                        }))
                      }
                      className="w-16 shrink-0"
                    />
                  </div>
                );
              })}
            </div>
            {startError && (
              <p className="text-sm text-destructive">{startError}</p>
            )}
            <Button
              onClick={handleStartInterview}
              disabled={isStarting}
              className="w-fit"
            >
              {isStarting ? "Starting…" : "Start interview"}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function ResumeDetailPage({
  params,
}: {
  params: Promise<{ resumeId: string }>;
}) {
  const { resumeId } = use(params);

  return (
    <ProtectedRoute>
      <ResumeDetail resumeId={Number(resumeId)} />
    </ProtectedRoute>
  );
}
