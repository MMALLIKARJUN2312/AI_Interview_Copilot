"use client";

import {
  FileText,
  Inbox,
  KeyRound,
  LogOut,
  MessagesSquare,
  Plus,
  ShieldCheck,
  Trash2,
  UserRound
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type {
  InterviewSessionStatus,
  InterviewStatistics,
  ResumeSummary,
  SessionSummary,
} from "@/lib/types";
const DASHBOARD_PAGE_SIZE = 10;
type SessionStatusFilter =
  | "all"
  | InterviewSessionStatus;

function appendUniqueById<T extends { id: number }>(
  currentItems: T[],
  newItems: T[],
): T[] {
  const itemsById = new Map(
    currentItems.map((item) => [item.id, item]),
  );

  for (const item of newItems) {
    itemsById.set(item.id, item);
  }

  return Array.from(itemsById.values());
}

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
  const router = useRouter();
  const {
    user,
    changePassword,
    deleteAccount,
    logoutAll,
    updateProfile,
  } = useAuth();

  const [resumes, setResumes] =
    useState<ResumeSummary[] | null>(null);
  const [sessionStatusFilter, setSessionStatusFilter] =
    useState<SessionStatusFilter>("all");
  const [sessions, setSessions] =
    useState<SessionSummary[] | null>(null);
    const [statistics, setStatistics] =
  useState<InterviewStatistics | null>(null);
const [isStatisticsLoading, setIsStatisticsLoading] =
  useState(true);
    const [hasMoreResumes, setHasMoreResumes] = useState(false);
const [hasMoreSessions, setHasMoreSessions] = useState(false);

const [isLoadingMoreResumes, setIsLoadingMoreResumes] =
  useState(false);
const [isLoadingMoreSessions, setIsLoadingMoreSessions] =
  useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSigningOutAll, setIsSigningOutAll] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [profileFullName, setProfileFullName] =
  useState(user?.full_name ?? "");
const [profileError, setProfileError] =
  useState<string | null>(null);
const [profileSuccess, setProfileSuccess] =
  useState<string | null>(null);
const [isUpdatingProfile, setIsUpdatingProfile] =
  useState(false);
  const [deletePassword, setDeletePassword] =
  useState("");
const [deleteConfirmation, setDeleteConfirmation] =
  useState("");
const [deleteError, setDeleteError] =
  useState<string | null>(null);
const [isDeletingAccount, setIsDeletingAccount] =
  useState(false);

useEffect(() => {
  let cancelled = false;

  async function loadResumes(): Promise<void> {
    try {
      const resumeList = await api.listResumes({
        limit: DASHBOARD_PAGE_SIZE,
        offset: 0,
      });

      if (cancelled) {
        return;
      }

      setResumes(resumeList);
      setHasMoreResumes(
        resumeList.length === DASHBOARD_PAGE_SIZE,
      );
    } catch {
      if (!cancelled) {
        setResumes([]);
        setError("Unable to load your resumes right now.");
      }
    }
  }

  void loadResumes();

  return () => {
    cancelled = true;
  };
}, []);

useEffect(() => {
  let cancelled = false;

  async function loadStatistics(): Promise<void> {
    setIsStatisticsLoading(true);

    try {
      const result =
        await api.getInterviewStatistics();

      if (!cancelled) {
        setStatistics(result);
      }
    } catch (error) {
      if (!cancelled) {
        setStatistics(null);
        setError(
          error instanceof ApiError
            ? error.message
            : "Unable to load your progress summary.",
        );
      }
    } finally {
      if (!cancelled) {
        setIsStatisticsLoading(false);
      }
    }
  }

  void loadStatistics();

  return () => {
    cancelled = true;
  };
}, []);

useEffect(() => {
  let cancelled = false;

  async function loadSessions(): Promise<void> {
    setSessions(null);
    setError(null);

    try {
      const sessionList = await api.listSessions({
        limit: DASHBOARD_PAGE_SIZE,
        offset: 0,
        ...(sessionStatusFilter === "all"
          ? {}
          : { status: sessionStatusFilter }),
      });

      if (cancelled) {
        return;
      }

      setSessions(sessionList);
      setHasMoreSessions(
        sessionList.length === DASHBOARD_PAGE_SIZE,
      );
    } catch {
      if (!cancelled) {
        setSessions([]);
        setHasMoreSessions(false);
        setError(
          "Unable to load your interview sessions right now.",
        );
      }
    }
  }

  void loadSessions();

  return () => {
    cancelled = true;
  };
}, [sessionStatusFilter]);

async function handleLoadMoreResumes(): Promise<void> {
  if (
    resumes === null ||
    isLoadingMoreResumes ||
    !hasMoreResumes
  ) {
    return;
  }

  setError(null);
  setIsLoadingMoreResumes(true);

  try {
    const nextPage = await api.listResumes({
      limit: DASHBOARD_PAGE_SIZE,
      offset: resumes.length,
    });

    setResumes((currentResumes) =>
      currentResumes === null
        ? nextPage
        : appendUniqueById(currentResumes, nextPage),
    );

    setHasMoreResumes(
      nextPage.length === DASHBOARD_PAGE_SIZE,
    );
  } catch (error) {
    setError(
      error instanceof ApiError
        ? error.message
        : "Unable to load more resumes. Please try again.",
    );
  } finally {
    setIsLoadingMoreResumes(false);
  }
}

async function handleLoadMoreSessions(): Promise<void> {
  if (
    sessions === null ||
    isLoadingMoreSessions ||
    !hasMoreSessions
  ) {
    return;
  }

  setError(null);
  setIsLoadingMoreSessions(true);

  try {
    const nextPage = await api.listSessions({
  limit: DASHBOARD_PAGE_SIZE,
  offset: sessions.length,
  ...(sessionStatusFilter === "all"
    ? {}
    : { status: sessionStatusFilter }),
});

    setSessions((currentSessions) =>
      currentSessions === null
        ? nextPage
        : appendUniqueById(currentSessions, nextPage),
    );

    setHasMoreSessions(
      nextPage.length === DASHBOARD_PAGE_SIZE,
    );
  } catch (error) {
    setError(
      error instanceof ApiError
        ? error.message
        : "Unable to load more interview sessions. Please try again.",
    );
  } finally {
    setIsLoadingMoreSessions(false);
  }
}

  async function handleLogoutAll(): Promise<void> {
    const confirmed = window.confirm(
      "Sign out from every device and browser? You will need to log in again.",
    );

    if (!confirmed) {
      return;
    }

    setError(null);
    setIsSigningOutAll(true);

    try {
      await logoutAll();
      router.replace("/login");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to sign out all sessions. Please try again.",
      );
    } finally {
      setIsSigningOutAll(false);
    }
  }

  async function handleUpdateProfile(
  event: FormEvent<HTMLFormElement>,
): Promise<void> {
  event.preventDefault();

  const normalizedName = profileFullName.trim();

  setProfileError(null);
  setProfileSuccess(null);

  if (
    normalizedName.length < 2 ||
    normalizedName.length > 100
  ) {
    setProfileError(
      "Your name must contain between 2 and 100 characters.",
    );
    return;
  }

  setIsUpdatingProfile(true);

  try {
    await updateProfile(normalizedName);
    setProfileFullName(normalizedName);
    setProfileSuccess("Profile updated successfully.");
  } catch (error) {
    setProfileError(
      error instanceof ApiError
        ? error.message
        : "Unable to update your profile. Please try again.",
    );
  } finally {
    setIsUpdatingProfile(false);
  }
}

  async function handleChangePassword(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setPasswordError(null);

    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }

    setIsChangingPassword(true);

    try {
      await changePassword(
        currentPassword,
        newPassword,
      );

      router.replace("/login");
    } catch (error) {
      setPasswordError(
        error instanceof ApiError
          ? error.message
          : "Unable to change your password. Please try again.",
      );
    } finally {
      setIsChangingPassword(false);
    }
  }

  async function handleDeleteAccount(
  event: FormEvent<HTMLFormElement>,
): Promise<void> {
  event.preventDefault();
  setDeleteError(null);

  if (deleteConfirmation !== "DELETE") {
    setDeleteError(
      'Enter the exact word "DELETE" to confirm.',
    );
    return;
  }

  setIsDeletingAccount(true);

  try {
    await deleteAccount(deletePassword);
    router.replace("/login");
  } catch (error) {
    setDeleteError(
      error instanceof ApiError
        ? error.message
        : "Unable to delete your account. Please try again.",
    );
  } finally {
    setIsDeletingAccount(false);
  }
}

  return (
    <div className="mx-auto w-full max-w-4xl flex-1 px-4 py-10">
      <div className="animate-fade-in-up mb-8 flex items-center justify-between">
        <h1 className="font-heading text-2xl font-semibold tracking-tight">Dashboard</h1>
        <Button asChild>
          <Link href="/resume/new">
            <Plus className="size-4" />
            Upload resume
          </Link>
        </Button>
      </div>

      <section
  aria-labelledby="progress-summary-heading"
  className="mb-8"
>
  <h2
    id="progress-summary-heading"
    className="sr-only"
  >
    Interview progress summary
  </h2>

  {isStatisticsLoading ? (
    <p className="text-sm text-muted-foreground">
      Loading progress summary…
    </p>
  ) : statistics ? (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">
            Total interviews
          </p>
          <p className="mt-1 text-2xl font-semibold">
            {statistics.total_sessions}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">
            In progress
          </p>
          <p className="mt-1 text-2xl font-semibold">
            {statistics.in_progress_sessions}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">
            Completed
          </p>
          <p className="mt-1 text-2xl font-semibold">
            {statistics.completed_sessions}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">
            Average score
          </p>
          <p className="mt-1 text-2xl font-semibold">
            {statistics.average_score === null
              ? "—"
              : `${statistics.average_score.toFixed(1)}/100`}
          </p>
        </CardContent>
      </Card>
    </div>
  ) : null}
</section>

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
<>
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

  {hasMoreResumes && (
    <div className="mt-4 flex justify-center">
      <Button
        type="button"
        variant="outline"
        disabled={isLoadingMoreResumes}
        onClick={() => void handleLoadMoreResumes()}
      >
        {isLoadingMoreResumes
          ? "Loading resumes…"
          : "Load more resumes"}
      </Button>
    </div>
  )}
</>
        )}
      </section>

      <section className="mb-10">
        <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
  <h2 className="flex items-center gap-2 text-lg font-medium">
    <MessagesSquare className="size-4 text-muted-foreground" />
    Interview sessions
  </h2>

  <div>
    <Label
      htmlFor="session-status-filter"
      className="sr-only"
    >
      Filter interview sessions by status
    </Label>

    <select
      id="session-status-filter"
      value={sessionStatusFilter}
      onChange={(event) =>
        setSessionStatusFilter(
          event.target.value as SessionStatusFilter,
        )
      }
      className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <option value="all">All interviews</option>
      <option value="in_progress">In progress</option>
      <option value="completed">Completed</option>
      <option value="abandoned">Abandoned</option>
    </select>
  </div>
</div>
        {sessions === null ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : sessions.length === 0 ? (
          <EmptyState
  icon={MessagesSquare}
  message={
    sessionStatusFilter === "all"
      ? "No mock interviews yet. Start one from a resume's page."
      : `No ${sessionStatusFilter.replace("_", " ")} interviews found.`
  }
/>
        ) : (
<>
  <div className="grid gap-3 sm:grid-cols-2">
    {sessions.map((session, index) => (
      <Link
        key={session.id}
        href={`/interview/${session.id}`}
      >
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

  {hasMoreSessions && (
    <div className="mt-4 flex justify-center">
      <Button
        type="button"
        variant="outline"
        disabled={isLoadingMoreSessions}
        onClick={() => void handleLoadMoreSessions()}
      >
        {isLoadingMoreSessions
          ? "Loading interviews…"
          : "Load more interviews"}
      </Button>
    </div>
  )}
</>
        )}
      </section>
      <section className="mb-10">
  <h2 className="mb-3 flex items-center gap-2 text-lg font-medium">
    <UserRound className="size-4 text-muted-foreground" />
    Profile
  </h2>

  <Card>
    <CardHeader>
      <CardTitle className="text-base">
        Display name
      </CardTitle>
      <CardDescription>
        This name is displayed throughout your account.
        Updating it does not change your login email.
      </CardDescription>
    </CardHeader>

    <CardContent>
      <form
        className="flex max-w-md flex-col gap-4"
        onSubmit={handleUpdateProfile}
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="profile-full-name">
            Full name
          </Label>

          <Input
            id="profile-full-name"
            name="fullName"
            type="text"
            autoComplete="name"
            minLength={2}
            maxLength={100}
            required
            value={profileFullName}
            onChange={(event) => {
              setProfileFullName(event.target.value);
              setProfileError(null);
              setProfileSuccess(null);
            }}
          />
        </div>

        <div>
          <p className="text-sm text-muted-foreground">
            Login email: {user?.email}
          </p>
        </div>

        {profileError && (
          <p
            role="alert"
            className="text-sm text-destructive"
          >
            {profileError}
          </p>
        )}

        {profileSuccess && (
          <p
            role="status"
            className="text-sm text-emerald-600 dark:text-emerald-400"
          >
            {profileSuccess}
          </p>
        )}

        <Button
          type="submit"
          className="w-fit"
          disabled={
            isUpdatingProfile ||
            profileFullName.trim().length < 2 ||
            profileFullName.trim() === user?.full_name
          }
        >
          {isUpdatingProfile
            ? "Saving profile…"
            : "Save profile"}
        </Button>
      </form>
    </CardContent>
  </Card>
</section>
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-medium">
          <ShieldCheck className="size-4 text-muted-foreground" />
          Account security
        </h2>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <KeyRound className="size-4" />
                Change password
              </CardTitle>
              <CardDescription>
                Changing your password signs you out from every
                device for your protection.
              </CardDescription>
            </CardHeader>

            <CardContent>
              <form
                className="flex flex-col gap-4"
                onSubmit={handleChangePassword}
              >
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="current-password">
                    Current password
                  </Label>
                  <Input
                    id="current-password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={currentPassword}
                    onChange={(event) =>
                      setCurrentPassword(event.target.value)
                    }
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="new-password">
                    New password
                  </Label>
                  <Input
                    id="new-password"
                    type="password"
                    autoComplete="new-password"
                    minLength={8}
                    required
                    value={newPassword}
                    onChange={(event) =>
                      setNewPassword(event.target.value)
                    }
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="confirm-password">
                    Confirm new password
                  </Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    autoComplete="new-password"
                    minLength={8}
                    required
                    value={confirmPassword}
                    onChange={(event) =>
                      setConfirmPassword(event.target.value)
                    }
                  />
                </div>

                {passwordError && (
                  <p className="text-sm text-destructive">
                    {passwordError}
                  </p>
                )}

                <Button
                  type="submit"
                  disabled={isChangingPassword}
                >
                  {isChangingPassword
                    ? "Changing password…"
                    : "Change password"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Active sessions
              </CardTitle>
              <CardDescription>
                If you used a shared computer or do not recognize a
                session, sign out from every device.
              </CardDescription>
            </CardHeader>

            <CardContent>
              <Button
                type="button"
                variant="destructive"
                disabled={isSigningOutAll}
                onClick={handleLogoutAll}
              >
                <LogOut className="size-4" />
                {isSigningOutAll
                  ? "Signing out…"
                  : "Sign out all devices"}
              </Button>
            </CardContent>
          </Card>
        </div>
        <Card className="mt-4 border-destructive/40">
  <CardHeader>
    <CardTitle className="flex items-center gap-2 text-base text-destructive">
      <Trash2 className="size-4" />
      Delete account
    </CardTitle>

    <CardDescription>
      Permanently delete your account, uploaded resumes,
      analyses, interview sessions, feedback and active
      sessions. This action cannot be undone.
    </CardDescription>
  </CardHeader>

  <CardContent>
    <form
      className="flex max-w-md flex-col gap-4"
      onSubmit={handleDeleteAccount}
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="delete-account-password">
          Current password
        </Label>

        <Input
          id="delete-account-password"
          type="password"
          autoComplete="current-password"
          required
          value={deletePassword}
          onChange={(event) =>
            setDeletePassword(event.target.value)
          }
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="delete-account-confirmation">
          Enter DELETE to confirm
        </Label>

        <Input
          id="delete-account-confirmation"
          type="text"
          autoComplete="off"
          required
          placeholder="DELETE"
          value={deleteConfirmation}
          onChange={(event) =>
            setDeleteConfirmation(event.target.value)
          }
        />
      </div>

      {deleteError && (
        <p
          role="alert"
          className="text-sm text-destructive"
        >
          {deleteError}
        </p>
      )}

      <Button
        type="submit"
        variant="destructive"
        disabled={
          isDeletingAccount ||
          !deletePassword ||
          deleteConfirmation !== "DELETE"
        }
      >
        <Trash2 className="size-4" />
        {isDeletingAccount
          ? "Deleting account…"
          : "Permanently delete account"}
      </Button>
    </form>
  </CardContent>
</Card>
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
