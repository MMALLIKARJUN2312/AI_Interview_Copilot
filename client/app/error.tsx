"use client";

import type { ErrorInfo } from "next/error";
import { CircleAlert, House, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";

// Define the correct Next.js global error page props
interface ErrorPageProps {
  error: Error & { digest?: string };
  unstable_retry: () => void; 
}

export default function ErrorPage({
  error,
  unstable_retry,
}: ErrorPageProps) {
  useEffect(() => {
    console.error("Route rendering failed", error);
  }, [error]);

  return (
    <section
      className="mx-auto flex w-full max-w-xl flex-1 flex-col items-center justify-center px-4 py-20 text-center"
      role="alert"
      aria-live="assertive"
    >
      <div className="glass-strong w-full rounded-2xl p-8 sm:p-10">
        <div className="mx-auto mb-5 flex size-14 items-center justify-center rounded-2xl bg-destructive/10">
          <CircleAlert
            className="size-7 text-destructive"
            aria-hidden="true"
          />
        </div>

        <h1 className="font-heading text-2xl font-semibold tracking-tight sm:text-3xl">
          Something went wrong
        </h1>

        <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-muted-foreground">
          We could not load this page. The problem may be temporary, so
          you can try again safely.
        </p>

        {error.digest && (
          <p className="mt-4 text-xs text-muted-foreground">
            Reference:{" "}
            <code className="rounded bg-muted px-1.5 py-0.5">
              {error.digest}
            </code>
          </p>
        )}

        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <Button
            type="button"
            size="lg"
            onClick={() => unstable_retry()}
          >
            <RefreshCw className="size-4" />
            Try again
          </Button>

          <Button
            asChild
            size="lg"
            variant="outline"
          >
            <Link href="/">
              <House className="size-4" />
              Return home
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}