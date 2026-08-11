"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { ProtectedRoute } from "@/components/protected-route";
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
import { Textarea } from "@/components/ui/textarea";
import { ApiError, api } from "@/lib/api";

function UploadResumeForm() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [targetRole, setTargetRole] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!file) {
      setError("Please choose a PDF resume to upload.");
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await api.uploadResume({
        file,
        targetRole,
        jobDescription: jobDescription || undefined,
      });
      router.push(`/resume/${result.resume_id}`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Upload failed. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-xl flex-1 px-4 py-10">
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Upload your resume</CardTitle>
          <CardDescription>
            We analyze your resume specifically against the role you&apos;re
            targeting, and use it to generate a matching mock interview.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="target_role">Target role</Label>
              <Input
                id="target_role"
                placeholder="e.g. Backend Engineer"
                required
                minLength={2}
                value={targetRole}
                onChange={(event) => setTargetRole(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="job_description">
                Job description (optional)
              </Label>
              <Textarea
                id="job_description"
                placeholder="Paste the job posting for a more precise analysis"
                rows={5}
                value={jobDescription}
                onChange={(event) => setJobDescription(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="file">Resume (PDF)</Label>
              <Input
                id="file"
                type="file"
                accept="application/pdf"
                required
                onChange={(event) =>
                  setFile(event.target.files?.[0] ?? null)
                }
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={isSubmitting} className="mt-2">
              {isSubmitting ? "Analyzing…" : "Analyze resume"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default function NewResumePage() {
  return (
    <ProtectedRoute>
      <UploadResumeForm />
    </ProtectedRoute>
  );
}
