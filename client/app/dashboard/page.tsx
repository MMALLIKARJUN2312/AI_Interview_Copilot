"use client";

import {
  FileText,
  Inbox,
  KeyRound,
  LogOut,
  MessagesSquare,
  Plus,
  ShieldCheck,
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
  ResumeSummary,
  SessionSummary,
} from "@/lib/types";

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
  const { changePassword, logoutAll } = useAuth();

  const [resumes, setResumes] =
    useState<ResumeSummary[] | null>(null);
  const [sessions, setSessions] =
    useState<SessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSigningOutAll, setIsSigningOutAll] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  useEffect(() => {
    Promise.all([api.listResumes(), api.listSessions()])
      .then(([resumeList, sessionList]) => {
        setResumes(resumeList);
        setSessions(sessionList);
      })
      .catch(() => setError("Unable to load your dashboard right now."));
  }, []);

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

      <section className="mb-10">
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
