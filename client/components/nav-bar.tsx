"use client";

import { Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/lib/auth-context";

export function NavBar() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <header className="glass sticky top-0 z-40 border-x-0 border-t-0">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="font-heading flex items-center gap-2 font-semibold tracking-tight">
          <span className="flex size-7 items-center justify-center rounded-lg bg-[linear-gradient(135deg,var(--brand-from),var(--brand-to))] text-primary-foreground shadow-sm">
            <Sparkles className="size-4" />
          </span>
          <span className="hidden sm:inline">AI Interview Copilot</span>
        </Link>

        <nav className="flex items-center gap-2">
          {!isLoading && user && (
            <>
              <Link
                href="/dashboard"
                className="px-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Dashboard
              </Link>
              <span
                className="hidden px-2 text-sm text-muted-foreground sm:inline"
                title={user.email}
              >
                {user.full_name}
              </span>
              <ThemeToggle />
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Log out
              </Button>
            </>
          )}

          {!isLoading && !user && (
            <>
              <ThemeToggle />
              <Button variant="ghost" size="sm" asChild>
                <Link href="/login">Log in</Link>
              </Button>
              <Button size="sm" asChild>
                <Link href="/register">Sign up</Link>
              </Button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
