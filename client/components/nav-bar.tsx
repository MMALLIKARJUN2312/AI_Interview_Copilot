"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

export function NavBar() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="font-semibold tracking-tight">
          AI Interview Copilot
        </Link>

        <nav className="flex items-center gap-2">
          {!isLoading && user && (
            <>
              <Link
                href="/dashboard"
                className="px-2 text-sm text-muted-foreground hover:text-foreground"
              >
                Dashboard
              </Link>
              <span className="hidden px-2 text-sm text-muted-foreground sm:inline">
                {user.email}
              </span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Log out
              </Button>
            </>
          )}

          {!isLoading && !user && (
            <>
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
