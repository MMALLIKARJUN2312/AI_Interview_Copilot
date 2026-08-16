import type {
  CompleteInterviewResponse,
  ResumeAnalysisResponse,
  ResumeSummary,
  RoundConfig,
  RunCodeResponse,
  SessionDetailResponse,
  SessionSummary,
  StartInterviewResponse,
  SubmitAnswerResponse,
  TokenResponse,
  UserResponse,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ACCESS_TOKEN_KEY = "aic_access_token";
const REFRESH_TOKEN_KEY = "aic_refresh_token";
const AUTH_EXPIRED_EVENT = "aic:auth-expired";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/** Fires when a refresh attempt fails, so the app can force a logout. */
export function onAuthExpired(handler: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(AUTH_EXPIRED_EVENT, handler);
  return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handler);
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  if (!refreshInFlight) {
    refreshInFlight = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (response) => {
        if (!response.ok) return null;
        const body = (await response.json()) as TokenResponse;
        setTokens(body.access_token, body.refresh_token);
        return body.access_token;
      })
      .catch(() => null)
      .finally(() => {
        refreshInFlight = null;
      });
  }

  return refreshInFlight;
}

async function doFetch(path: string, options: RequestInit): Promise<Response> {
  const token = getToken();
  const headers = new Headers(options.headers);

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(`${API_BASE_URL}${path}`, { ...options, headers });
}

const AUTH_ENDPOINTS = ["/auth/login", "/auth/register", "/auth/refresh"];

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response = await doFetch(path, options);

  if (response.status === 401 && !AUTH_ENDPOINTS.includes(path)) {
    const newAccessToken = await refreshAccessToken();

    if (newAccessToken) {
      response = await doFetch(path, options);
    } else {
      clearToken();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
      }
    }
  }

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

  logout() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return Promise.resolve();

    return request<{ message: string }>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
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

  startInterview(payload: { resumeId: number; rounds?: RoundConfig[] }) {
    return request<StartInterviewResponse>("/interview/start", {
      method: "POST",
      body: JSON.stringify({
        resume_id: payload.resumeId,
        ...(payload.rounds ? { rounds: payload.rounds } : {}),
      }),
    });
  },

  submitAnswer(payload: {
    sessionId: number;
    questionId: number;
    answerText?: string;
    code?: string;
    language?: string;
  }) {
    return request<SubmitAnswerResponse>(
      `/interview/${payload.sessionId}/answer`,
      {
        method: "POST",
        body: JSON.stringify({
          question_id: payload.questionId,
          answer_text: payload.answerText ?? null,
          code: payload.code ?? null,
          language: payload.language ?? null,
        }),
      },
    );
  },

  runCode(payload: {
    sessionId: number;
    questionId: number;
    code: string;
    language: string;
  }) {
    return request<RunCodeResponse>(`/interview/${payload.sessionId}/run-code`, {
      method: "POST",
      body: JSON.stringify({
        question_id: payload.questionId,
        code: payload.code,
        language: payload.language,
      }),
    });
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
