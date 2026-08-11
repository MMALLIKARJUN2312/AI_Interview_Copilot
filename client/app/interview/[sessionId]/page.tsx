"use client";

import { use, useEffect, useState } from "react";

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
import { Textarea } from "@/components/ui/textarea";
import { ApiError, api } from "@/lib/api";
import type {
  AnswerResponse,
  FeedbackResponse,
  QuestionResponse,
  RoadmapResponse,
  SessionSummary,
} from "@/lib/types";

type Phase =
  | "loading"
  | "error"
  | "answering"
  | "reviewing_answer"
  | "ready_to_complete"
  | "completed";

function ScoreList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;

  return (
    <div>
      <h3 className="mb-2 text-sm font-medium">{title}</h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function InterviewFlow({ sessionId }: { sessionId: number }) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<SessionSummary | null>(null);
  const [currentQuestion, setCurrentQuestion] =
    useState<QuestionResponse | null>(null);
  const [answerText, setAnswerText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastAnswer, setLastAnswer] = useState<AnswerResponse | null>(null);
  const [pendingNextQuestion, setPendingNextQuestion] =
    useState<QuestionResponse | null>(null);
  const [pendingIsComplete, setPendingIsComplete] = useState(false);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [feedback, setFeedback] = useState<FeedbackResponse | null>(null);
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);

  useEffect(() => {
    api
      .getSessionDetail(sessionId)
      .then((detail) => {
        setSession(detail.session);
        setTotalQuestions(detail.session.total_questions);

        const sorted = [...detail.questions].sort(
          (a, b) => a.order_index - b.order_index,
        );
        const answered = sorted.filter((question) => question.answer);
        setAnsweredCount(answered.length);

        if (detail.session.status === "completed") {
          setFeedback(detail.feedback);
          setRoadmap(detail.roadmap);
          setPhase("completed");
          return;
        }

        const next = sorted.find((question) => !question.answer) ?? null;

        if (next) {
          setCurrentQuestion(next);
          setPhase("answering");
        } else {
          setPhase("ready_to_complete");
        }
      })
      .catch(() => {
        setError("Unable to load this interview session.");
        setPhase("error");
      });
  }, [sessionId]);

  async function handleSubmitAnswer() {
    if (!currentQuestion || !answerText.trim()) return;

    setError(null);
    setIsSubmitting(true);

    try {
      const result = await api.submitAnswer({
        sessionId,
        questionId: currentQuestion.id,
        answerText,
      });

      setLastAnswer(result.answer);
      setPendingNextQuestion(result.next_question);
      setPendingIsComplete(result.is_complete);
      setAnsweredCount((count) => count + 1);
      setPhase("reviewing_answer");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not submit your answer. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleContinue() {
    setAnswerText("");
    setLastAnswer(null);

    if (pendingNextQuestion) {
      setCurrentQuestion(pendingNextQuestion);
      setPendingNextQuestion(null);
      setPhase("answering");
    } else if (pendingIsComplete) {
      setPhase("ready_to_complete");
    }
  }

  async function handleCompleteInterview() {
    setError(null);
    setIsSubmitting(true);

    try {
      const result = await api.completeInterview(sessionId);
      setSession(result.session);
      setFeedback(result.feedback);
      setRoadmap(result.roadmap);
      setPhase("completed");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not complete the interview. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (phase === "loading") {
    return (
      <div className="mx-auto w-full max-w-2xl flex-1 px-4 py-10 text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="mx-auto w-full max-w-2xl flex-1 px-4 py-10">
        <p className="text-sm text-destructive">{error}</p>
      </div>
    );
  }

  if (phase === "completed") {
    return (
      <div className="mx-auto w-full max-w-2xl flex-1 px-4 py-10">
        <h1 className="mb-1 text-2xl font-semibold tracking-tight">
          Interview complete
        </h1>
        <p className="mb-6 text-sm text-muted-foreground">
          {session?.target_role}
        </p>

        {feedback && (
          <Card className="mb-6">
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <CardTitle>Overall performance</CardTitle>
                <Badge variant="success">{feedback.overall_score}/100</Badge>
              </div>
              <CardDescription>{feedback.summary}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-5">
              <ScoreList title="Strengths" items={feedback.strengths} />
              <ScoreList title="Weaknesses" items={feedback.weaknesses} />
              <div>
                <h3 className="mb-2 text-sm font-medium">Recommendation</h3>
                <p className="text-sm text-muted-foreground">
                  {feedback.recommendation}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {roadmap && roadmap.items.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Your learning roadmap</CardTitle>
              <CardDescription>
                Prioritized next steps to close the gaps above.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {roadmap.items.map((item, index) => (
                <div
                  key={index}
                  className="rounded-lg border border-border p-3"
                >
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <h4 className="font-medium">{item.topic}</h4>
                    <Badge
                      variant={
                        item.priority === "high"
                          ? "destructive"
                          : item.priority === "medium"
                            ? "secondary"
                            : "outline"
                      }
                    >
                      {item.priority}
                    </Badge>
                  </div>
                  <p className="mb-2 text-sm text-muted-foreground">
                    {item.description}
                  </p>
                  {item.resources.length > 0 && (
                    <ul className="list-disc space-y-0.5 pl-5 text-sm text-muted-foreground">
                      {item.resources.map((resource, resourceIndex) => (
                        <li key={resourceIndex}>{resource}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-2xl flex-1 px-4 py-10">
      <div className="mb-6 flex items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Mock interview
          </h1>
          <p className="text-sm text-muted-foreground">
            {session?.target_role}
          </p>
        </div>
        <Badge variant="secondary">
          {answeredCount}/{totalQuestions} answered
        </Badge>
      </div>

      {error && <p className="mb-4 text-sm text-destructive">{error}</p>}

      {phase === "answering" && currentQuestion && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{currentQuestion.category}</Badge>
              <Badge variant="outline">{currentQuestion.difficulty}</Badge>
            </div>
            <CardTitle className="text-lg font-normal">
              {currentQuestion.question_text}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Textarea
              rows={7}
              placeholder="Type your answer…"
              value={answerText}
              onChange={(event) => setAnswerText(event.target.value)}
            />
            <Button
              onClick={handleSubmitAnswer}
              disabled={isSubmitting || !answerText.trim()}
              className="w-fit"
            >
              {isSubmitting ? "Submitting…" : "Submit answer"}
            </Button>
          </CardContent>
        </Card>
      )}

      {phase === "reviewing_answer" && lastAnswer && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle>Answer feedback</CardTitle>
              <Badge variant="success">{lastAnswer.score}/100</Badge>
            </div>
            <CardDescription>{lastAnswer.feedback}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            <ScoreList title="Strengths" items={lastAnswer.strengths} />
            <ScoreList title="Areas to improve" items={lastAnswer.improvements} />
            <Button onClick={handleContinue} className="w-fit">
              {pendingIsComplete ? "Continue" : "Next question"}
            </Button>
          </CardContent>
        </Card>
      )}

      {phase === "ready_to_complete" && (
        <Card>
          <CardHeader>
            <CardTitle>All questions answered</CardTitle>
            <CardDescription>
              Generate your overall feedback and learning roadmap.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={handleCompleteInterview}
              disabled={isSubmitting}
              className="w-fit"
            >
              {isSubmitting ? "Generating…" : "See my results"}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function InterviewSessionPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = use(params);

  return (
    <ProtectedRoute>
      <InterviewFlow sessionId={Number(sessionId)} />
    </ProtectedRoute>
  );
}
