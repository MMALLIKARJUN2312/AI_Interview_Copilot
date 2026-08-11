import type {
  CompleteInterviewResponse,
  ResumeAnalysisResponse,
  ResumeSummary,
  SessionDetailResponse,
  SessionSummary,
  StartInterviewResponse,
  SubmitAnswerResponse,
  TokenResponse,
  UserResponse,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TOKEN_KEY = "aic_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        message = body.detail;
      }
    } catch {
      // response body wasn't JSON; keep the default message
    }

    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  register(payload: { full_name: string; email: string; password: string }) {
    return request<{ message: string; user_id: number }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  login(payload: { email: string; password: string }) {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  me() {
    return request<UserResponse>("/auth/me");
  },

  uploadResume(payload: {
    file: File;
    targetRole: string;
    jobDescription?: string;
  }) {
    const formData = new FormData();
    formData.append("file", payload.file);
    formData.append("target_role", payload.targetRole);
    if (payload.jobDescription) {
      formData.append("job_description", payload.jobDescription);
    }

    return request<ResumeAnalysisResponse>("/resume/analyze", {
      method: "POST",
      body: formData,
    });
  },

  listResumes() {
    return request<ResumeSummary[]>("/resume/");
  },

  getResume(resumeId: number) {
    return request<ResumeSummary>(`/resume/${resumeId}`);
  },

  getResumeAnalysis(resumeId: number) {
    return request<ResumeAnalysisResponse>(`/resume/${resumeId}/analysis`);
  },

  startInterview(payload: { resumeId: number; numQuestions: number }) {
    return request<StartInterviewResponse>("/interview/start", {
      method: "POST",
      body: JSON.stringify({
        resume_id: payload.resumeId,
        num_questions: payload.numQuestions,
      }),
    });
  },

  submitAnswer(payload: {
    sessionId: number;
    questionId: number;
    answerText: string;
  }) {
    return request<SubmitAnswerResponse>(
      `/interview/${payload.sessionId}/answer`,
      {
        method: "POST",
        body: JSON.stringify({
          question_id: payload.questionId,
          answer_text: payload.answerText,
        }),
      },
    );
  },

  completeInterview(sessionId: number) {
    return request<CompleteInterviewResponse>(
      `/interview/${sessionId}/complete`,
      { method: "POST" },
    );
  },

  listSessions() {
    return request<SessionSummary[]>("/interview/sessions");
  },

  getSessionDetail(sessionId: number) {
    return request<SessionDetailResponse>(`/interview/${sessionId}`);
  },
};
