import type { CodeLanguage } from "@/lib/types";

const DRAFT_KEY_PREFIX = "aic:interview-draft";
const VALID_LANGUAGES: CodeLanguage[] = [
  "python",
  "javascript",
  "java",
  "cpp",
];

export interface InterviewDraft {
  answerText: string;
  code: string;
  language: CodeLanguage;
  updatedAt: string;
}

function createDraftKey(
  sessionId: number,
  questionId: number,
): string {
  return [
    DRAFT_KEY_PREFIX,
    sessionId,
    questionId,
  ].join(":");
}

function isCodeLanguage(
  value: unknown,
): value is CodeLanguage {
  return (
    typeof value === "string" &&
    VALID_LANGUAGES.includes(
      value as CodeLanguage,
    )
  );
}

export function loadInterviewDraft(
  sessionId: number,
  questionId: number,
): InterviewDraft | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const storedValue = window.sessionStorage.getItem(
      createDraftKey(sessionId, questionId),
    );

    if (!storedValue) {
      return null;
    }

    const parsed = JSON.parse(
      storedValue,
    ) as Partial<InterviewDraft>;

    if (
      typeof parsed.answerText !== "string" ||
      typeof parsed.code !== "string" ||
      !isCodeLanguage(parsed.language) ||
      typeof parsed.updatedAt !== "string"
    ) {
      clearInterviewDraft(
        sessionId,
        questionId,
      );
      return null;
    }

    return {
      answerText: parsed.answerText,
      code: parsed.code,
      language: parsed.language,
      updatedAt: parsed.updatedAt,
    };
  } catch {
    clearInterviewDraft(
      sessionId,
      questionId,
    );
    return null;
  }
}

export function saveInterviewDraft(
  sessionId: number,
  questionId: number,
  draft: Omit<InterviewDraft, "updatedAt">,
): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  if (
    !draft.answerText.trim() &&
    !draft.code.trim()
  ) {
    clearInterviewDraft(
      sessionId,
      questionId,
    );
    return false;
  }

  try {
    const value: InterviewDraft = {
      ...draft,
      updatedAt: new Date().toISOString(),
    };

    window.sessionStorage.setItem(
      createDraftKey(sessionId, questionId),
      JSON.stringify(value),
    );

    return true;
  } catch {
    // Interview submission still works if browser storage
    // is unavailable or its quota has been reached.
    return false;
  }
}

export function clearInterviewDraft(
  sessionId: number,
  questionId: number,
): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.sessionStorage.removeItem(
      createDraftKey(sessionId, questionId),
    );
  } catch {
    // Storage cleanup failure must not block the UI.
  }
}

export function clearInterviewSessionDrafts(
  sessionId: number,
): void {
  if (typeof window === "undefined") {
    return;
  }

  const sessionPrefix = [
    DRAFT_KEY_PREFIX,
    sessionId,
    "",
  ].join(":");

  try {
    for (
      let index =
        window.sessionStorage.length - 1;
      index >= 0;
      index -= 1
    ) {
      const key =
        window.sessionStorage.key(index);

      if (key?.startsWith(sessionPrefix)) {
        window.sessionStorage.removeItem(key);
      }
    }
  } catch {
    // Storage cleanup failure must not block the UI.
  }
}