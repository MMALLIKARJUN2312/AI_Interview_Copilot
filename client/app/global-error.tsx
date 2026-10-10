"use client";

import Link from 'next/link'
import type { ErrorInfo } from "next/error";
import { useEffect } from "react";

const pageStyle = {
  colorScheme: "light dark",
  minHeight: "100%",
  margin: 0,
  fontFamily:
    "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
} as const;

const bodyStyle = {
  minHeight: "100vh",
  margin: 0,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "24px",
  background:
    "linear-gradient(145deg, Canvas, color-mix(in srgb, Canvas 92%, #7567e8 8%))",
  color: "CanvasText",
} as const;

const cardStyle = {
  width: "100%",
  maxWidth: "520px",
  padding: "40px",
  border: "1px solid color-mix(in srgb, CanvasText 14%, transparent)",
  borderRadius: "18px",
  background: "Canvas",
  boxShadow: "0 20px 60px rgb(0 0 0 / 12%)",
  textAlign: "center",
} as const;

const primaryButtonStyle = {
  minHeight: "44px",
  padding: "0 20px",
  border: 0,
  borderRadius: "10px",
  background: "#6957d9",
  color: "#ffffff",
  fontSize: "15px",
  fontWeight: 600,
  cursor: "pointer",
} as const;

const secondaryLinkStyle = {
  display: "inline-flex",
  minHeight: "42px",
  alignItems: "center",
  padding: "0 18px",
  border: "1px solid color-mix(in srgb, CanvasText 20%, transparent)",
  borderRadius: "10px",
  color: "CanvasText",
  fontSize: "15px",
  fontWeight: 600,
  textDecoration: "none",
} as const;

// Define the correct Next.js global error page props
interface GlobalErrorPageProps {
  error: Error & { digest?: string };
  unstable_retry: () => void; 
}

export default function GlobalErrorPage({
  error,
  unstable_retry,
}: GlobalErrorPageProps) {
  useEffect(() => {
    console.error("Application rendering failed", error);
  }, [error]);

  return (
    <html lang="en" style={pageStyle}>
      <body style={bodyStyle}>
        <title>Application error | AI Interview Copilot</title>

        <main
          style={cardStyle}
          role="alert"
          aria-live="assertive"
        >
          <div
            aria-hidden="true"
            style={{
              fontSize: "42px",
              lineHeight: 1,
              marginBottom: "20px",
            }}
          >
            ⚠
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: "28px",
              lineHeight: 1.2,
            }}
          >
            AI Interview Copilot is temporarily unavailable
          </h1>

          <p
            style={{
              margin: "16px auto 0",
              maxWidth: "420px",
              lineHeight: 1.6,
              opacity: 0.72,
            }}
          >
            A critical page component could not be loaded. Try reloading
            the application or return to the home page.
          </p>

          {error.digest && (
            <p
              style={{
                marginTop: "16px",
                fontSize: "12px",
                opacity: 0.65,
              }}
            >
              Reference: {error.digest}
            </p>
          )}

          <div
            style={{
              marginTop: "28px",
              display: "flex",
              flexWrap: "wrap",
              justifyContent: "center",
              gap: "12px",
            }}
          >
            <button
              type="button"
              style={primaryButtonStyle}
              onClick={() => unstable_retry()}
            >
              Try again
            </button>

            <Link href="/" style={secondaryLinkStyle}>
              Return home
            </Link>
          </div>
        </main>
      </body>
    </html>
  );
}