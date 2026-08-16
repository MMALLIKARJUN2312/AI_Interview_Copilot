"use client";

import { Code2, Laptop2, MessagesSquare, PartyPopper, PlayCircle, Sparkle } from "lucide-react";
import { use, useEffect, useState } from "react";

import { CodeEditor, STARTER_TEMPLATES } from "@/components/code-editor";
import { ProtectedRoute } from "@/components/protected-route";
import { ScoreList } from "@/components/score-list";
import { ScoreRing } from "@/components/score-ring";
import { TestCaseResults } from "@/components/test-case-results";
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
  CodeLanguage,
  ExecutionResult,
  FeedbackResponse,
  QuestionResponse,
  RoadmapResponse,
  RoundType,
  SessionSummary,
} from "@/lib/types";

type Phase =
  | "loading"
  | "error"
  | "answering"
  | "reviewing_answer"
  | "ready_to_complete"
  | "completed";

const ROUND_META: Record<RoundType, { label: string; icon: typeof Code2 }> = {
  dsa_coding: { label: "DSA coding round", icon: Code2 },
  machine_coding: { label: "Machine coding round", icon: Laptop2 },
  general: { label: "General round", icon: MessagesSquare },
};

function ProgressBar({ answered, total }: { answered: number; total: number }) {
  const pct = total > 0 ? Math.min(100, (answered / total) * 100) : 0;

  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <div
        className="h-full rounded-full bg-[linear-gradient(90deg,var(--brand-from),var(--brand-to))] transition-[width] duration-500 ease-out"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function isCodingRound(question : QuestionResponse | null) {
  return question !== null && question.round_type !== "general";
}

function InterviewFlow({ sessionId }: { sessionId: number }) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<SessionSummary | null>(null);
  const [currentQuestion, setCurrentQuestion] =
    useState<QuestionResponse | null>(null);
  const [answerText, setAnswerText] = useState("");
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState<CodeLanguage>("python");
  const [runResults, setRunResults] = useState<ExecutionResult[] | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastAnswer, setLastAnswer] = useState<AnswerResponse | null>(null);
  const [pendingNextQuestion, setPendingNextQuestion] =
    useState<QuestionResponse | null>(null);
  const [pendingIsComplete, setPendingIsComplete] = useState(false);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [feedback, setFeedback] = useState<FeedbackResponse | null>(null);
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);

  function loadQuestion(question: QuestionResponse) {
    setCurrentQuestion(question);
    setAnswerText("");
    setRunResults(null);
    if (isCodingRound(question)) {
      setLanguage("python");
      setCode(STARTER_TEMPLATES.python);
    }
  }

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
          loadQuestion(next);
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

  async function handleRunCode() {
    if (!currentQuestion || !code.trim()) return;

    setError(null);
    setIsRunning(true);

    try {
      const result = await api.runCode({
        sessionId,
        questionId: currentQuestion.id,
        code,
        language,
      });
      setRunResults(result.results);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not run your code. Please try again.",
      );
    } finally {
      setIsRunning(false);
    }
  }

  async function handleSubmitAnswer() {
    if (!currentQuestion) return;
    const isCoding = isCodingRound(currentQuestion);
    if (isCoding && !code.trim()) return;
    if (!isCoding && !answerText.trim()) return;

    setError(null);
    setIsSubmitting(true);

    try {
      const result = await api.submitAnswer({
        sessionId,
        questionId: currentQuestion.id,
        ...(isCoding ? { code, language } : { answerText }),
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
    setLastAnswer(null);

    if (pendingNextQuestion) {
      loadQuestion(pendingNextQuestion);
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
        <div className="animate-fade-in-up mb-6 flex items-center gap-2">
          <PartyPopper className="size-6 text-[var(--brand-via)]" />
          <div>
            <h1 className="font-heading text-2xl font-semibold tracking-tight">
              Interview complete
            </h1>
            <p className="text-sm text-muted-foreground">
              {session?.target_role}
            </p>
          </div>
        </div>

        {feedback && (
          <Card className="animate-fade-in-up mb-6">
            <CardHeader>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <CardTitle>Overall performance</CardTitle>
                  <CardDescription className="mt-1">
                    {feedback.summary}
                  </CardDescription>
                </div>
                <ScoreRing score={feedback.overall_score} />
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-5">
              <ScoreList title="Strengths" items={feedback.strengths} kind="positive" />
              <ScoreList title="Weaknesses" items={feedback.weaknesses} kind="negative" />
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
          <Card className="animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
            <CardHeader>
              <CardTitle>Your learning roadmap</CardTitle>
              <CardDescription>
                Prioritized next steps to close the gaps above.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {roadmap.items.map((item, index) => (
                <div
                  key={index}
                  className="rounded-xl border border-border bg-background/40 p-4 transition-colors hover:bg-background/60"
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

  const roundMeta = currentQuestion ? ROUND_META[currentQuestion.round_type] : null;
  const RoundIcon = roundMeta?.icon ?? MessagesSquare;
  const wide = isCodingRound(currentQuestion) && phase === "answering";

  return (
    <div className={`mx-auto w-full flex-1 px-4 py-10 ${wide ? "max-w-4xl" : "max-w-2xl"}`}>
      <div className="animate-fade-in-up mb-3 flex items-center justify-between gap-2">
        <div>
          <h1 className="font-heading text-2xl font-semibold tracking-tight">
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

      <div className="animate-fade-in-up mb-6">
        <ProgressBar answered={answeredCount} total={totalQuestions} />
      </div>

      {error && <p className="mb-4 text-sm text-destructive">{error}</p>}

      {phase === "answering" && currentQuestion && (
        <Card className="animate-fade-in-up" key={currentQuestion.id}>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1">
                <RoundIcon className="size-3" />
                {roundMeta?.label}
              </Badge>
              <Badge variant="outline">{currentQuestion.difficulty}</Badge>
            </div>
            <CardTitle className="text-lg font-normal whitespace-pre-line">
              {currentQuestion.question_text}
            </CardTitle>
            {currentQuestion.examples && (
              <CardDescription className="mt-2 whitespace-pre-line">
                <span className="font-medium text-foreground">Examples: </span>
                {currentQuestion.examples}
              </CardDescription>
            )}
            {currentQuestion.constraints && (
              <CardDescription className="mt-1 whitespace-pre-line">
                <span className="font-medium text-foreground">Constraints: </span>
                {currentQuestion.constraints}
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {isCodingRound(currentQuestion) ? (
              <>
                <CodeEditor
                  language={language}
                  code={code}
                  onLanguageChange={setLanguage}
                  onCodeChange={setCode}
                />
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    onClick={handleRunCode}
                    disabled={isRunning || !code.trim()}
                    className="w-fit"
                  >
                    <PlayCircle className="size-4" />
                    {isRunning ? "Running…" : "Run"}
                  </Button>
                  <Button
                    onClick={handleSubmitAnswer}
                    disabled={isSubmitting || !code.trim()}
                    className="w-fit"
                  >
                    {isSubmitting ? "Submitting…" : "Submit"}
                  </Button>
                </div>
                {runResults && <TestCaseResults results={runResults} />}
              </>
            ) : (
              <>
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
              </>
            )}
          </CardContent>
        </Card>
      )}

      {phase === "reviewing_answer" && lastAnswer && (
        <Card className="animate-fade-in-up">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <Sparkle className="size-5 text-[var(--brand-via)]" />
                <CardTitle>Answer feedback</CardTitle>
              </div>
              <ScoreRing score={lastAnswer.score} size={64} label="" />
            </div>
            <CardDescription className="pt-1">{lastAnswer.feedback}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            {lastAnswer.total_test_count !== null && (
              <Badge variant={lastAnswer.passed_test_count === lastAnswer.total_test_count ? "success" : "secondary"}>
                {lastAnswer.passed_test_count}/{lastAnswer.total_test_count} test cases passed
              </Badge>
            )}
            {lastAnswer.execution_results && lastAnswer.execution_results.length > 0 && (
              <TestCaseResults results={lastAnswer.execution_results} />
            )}
            <ScoreList title="Strengths" items={lastAnswer.strengths} kind="positive" />
            <ScoreList title="Areas to improve" items={lastAnswer.improvements} kind="negative" />
            <Button onClick={handleContinue} className="w-fit">
              {pendingIsComplete ? "Continue" : "Next question"}
            </Button>
          </CardContent>
        </Card>
      )}

      {phase === "ready_to_complete" && (
        <Card className="animate-fade-in-up">
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
