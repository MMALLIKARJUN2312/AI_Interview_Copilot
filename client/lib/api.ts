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

const LEGACY_ACCESS_TOKEN_KEY = "aic_access_token";
const AUTH_EXPIRED_EVENT = "aic:auth-expired";

let accessToken: string | null = null;
let refreshInFlight: Promise<string | null> | null = null;

interface CsrfResponse {
  csrf_token: string;
}

interface ApiValidationError {
  loc?: Array<string | number>;
  msg?: string;
}

interface ApiErrorResponse {
  detail?: string | ApiValidationError[];
  message?: string;
}

function removeLegacyStoredToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
}

export function getToken(): string | null {
  return accessToken;
}

export function setToken(token: string): void {
  accessToken = token;

  // Remove tokens stored by versions released before access tokens
  // became memory-only.
  removeLegacyStoredToken();
}

export function clearToken(): void {
  accessToken = null;
  removeLegacyStoredToken();
}

/**
 * Subscribes to authentication-expired events.
 * Returns a cleanup function for React effects.
 */
export function onAuthExpired(handler: () => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }

  window.addEventListener(AUTH_EXPIRED_EVENT, handler);

  return () => {
    window.removeEventListener(AUTH_EXPIRED_EVENT, handler);
  };
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function formatValidationErrors(
  errors: ApiValidationError[],
): string | null {
  const messages = errors
    .map((error) => {
      if (typeof error.msg !== "string") {
        return null;
      }

      const location = Array.isArray(error.loc)
        ? error.loc
            .filter(
              (part) =>
                part !== "body" &&
                part !== "query" &&
                part !== "path",
            )
            .join(".")
        : "";

      return location
        ? `${location}: ${error.msg}`
        : error.msg;
    })
    .filter((message): message is string => Boolean(message));

  const uniqueMessages = [...new Set(messages)];

  return uniqueMessages.length > 0
    ? uniqueMessages.join("; ")
    : null;
}

async function getErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorResponse;

    if (typeof body.detail === "string") {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      const validationMessage = formatValidationErrors(body.detail);

      if (validationMessage) {
        return validationMessage;
      }
    }

    if (typeof body.message === "string") {
      return body.message;
    }
  } catch {
    // Keep the supplied fallback for non-JSON responses.
  }

  return fallback;
}

async function requestCsrfToken(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/auth/csrf`, {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
  const message = await getErrorMessage(
    response,
    "Unable to initialize secure authentication",
  );

  throw new ApiError(response.status, message);
}

  const body = (await response.json()) as CsrfResponse;

  if (!body.csrf_token) {
    throw new ApiError(500, "The server did not return a CSRF token");
  }

  return body.csrf_token;
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const csrfToken = await requestCsrfToken();

        const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
          method: "POST",
          credentials: "include",
          headers: {
            "X-CSRF-Token": csrfToken,
          },
        });

        if (!response.ok) {
          clearToken();
          return null;
        }

        const body = (await response.json()) as TokenResponse;

        if (!body.access_token) {
          clearToken();
          return null;
        }

        setToken(body.access_token);
        return body.access_token;
      } catch {
        clearToken();
        return null;
      }
    })().finally(() => {
      refreshInFlight = null;
    });
  }

  return refreshInFlight;
}

async function doFetch(
  path: string,
  options: RequestInit,
): Promise<Response> {
  const token = getToken();
  const headers = new Headers(options.headers);

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
}

const AUTH_ENDPOINTS = [
  "/auth/login",
  "/auth/register",
  "/auth/refresh",
];

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
  const message = await getErrorMessage(
    response,
    `Request failed with status ${response.status}`,
  );

  throw new ApiError(response.status, message);
}

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  register(payload: {
    full_name: string;
    email: string;
    password: string;
  }) {
    return request<{
      message: string;
      user_id: number;
    }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  restoreSession() {
    return refreshAccessToken();
  },

  login(payload: {
    email: string;
    password: string;
  }) {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async logout() {
    const csrfToken = await requestCsrfToken();

    return request<{ message: string }>("/auth/logout", {
      method: "POST",
      headers: {
        "X-CSRF-Token": csrfToken,
      },
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
    return request<ResumeAnalysisResponse>(
      `/resume/${resumeId}/analysis`,
    );
  },

  startInterview(payload: {
    resumeId: number;
    rounds?: RoundConfig[];
  }) {
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
    return request<RunCodeResponse>(
      `/interview/${payload.sessionId}/run-code`,
      {
        method: "POST",
        body: JSON.stringify({
          question_id: payload.questionId,
          code: payload.code,
          language: payload.language,
        }),
      },
    );
  },

  completeInterview(sessionId: number) {
    return request<CompleteInterviewResponse>(
      `/interview/${sessionId}/complete`,
      {
        method: "POST",
      },
    );
  },

  listSessions() {
    return request<SessionSummary[]>("/interview/sessions");
  },

  getSessionDetail(sessionId: number) {
    return request<SessionDetailResponse>(
      `/interview/${sessionId}`,
    );
  },
};