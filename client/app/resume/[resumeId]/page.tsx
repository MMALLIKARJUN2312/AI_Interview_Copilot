"use client";

import { MessagesSquare } from "lucide-react";
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
import { Label } from "@/components/ui/label";
import { ApiError, api } from "@/lib/api";
import type { ResumeAnalysisResponse, ResumeSummary } from "@/lib/types";

function ResumeDetail({ resumeId }: { resumeId: number }) {
  const router = useRouter();
  const [resume, setResume] = useState<ResumeSummary | null>(null);
  const [analysis, setAnalysis] = useState<ResumeAnalysisResponse | null>(
    null,
  );
  const [loadError, setLoadError] = useState<string | null>(null);
  const [numQuestions, setNumQuestions] = useState(5);
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
    setIsStarting(true);

    try {
      const result = await api.startInterview({ resumeId, numQuestions });
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
      <div className="mx-auto w-full max-w-2xl flex-1 px-4 py-10">
        <p className="text-sm text-destructive">{loadError}</p>
      </div>
    );
  }

  if (!resume) {
    return (
      <div className="mx-auto w-full max-w-2xl flex-1 px-4 py-10 text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-2xl flex-1 px-4 py-10">
      <div className="animate-fade-in-up mb-6 flex items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
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
              Questions will be generated from this resume and role.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="num_questions">Number of questions</Label>
              <Input
                id="num_questions"
                type="number"
                min={3}
                max={10}
                value={numQuestions}
                onChange={(event) =>
                  setNumQuestions(Number(event.target.value))
                }
                className="w-24"
              />
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
