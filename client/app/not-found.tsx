import { ArrowLeft, SearchX } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <section className="mx-auto flex w-full max-w-xl flex-1 flex-col items-center justify-center px-4 py-20 text-center">
      <div className="animate-fade-in-up glass-strong w-full rounded-2xl p-8 sm:p-10">
        <div className="mx-auto mb-5 flex size-14 items-center justify-center rounded-2xl bg-muted">
          <SearchX
            className="size-7 text-muted-foreground"
            aria-hidden="true"
          />
        </div>

        <p className="mb-2 text-sm font-medium text-primary">
          Error 404
        </p>

        <h1 className="font-heading text-2xl font-semibold tracking-tight sm:text-3xl">
          Page not found
        </h1>

        <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-muted-foreground">
          The page may have been moved, deleted, or the address may be
          incorrect.
        </p>

        <div className="mt-7 flex justify-center">
          <Button asChild size="lg">
            <Link href="/">
              <ArrowLeft className="size-4" />
              Return home
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}