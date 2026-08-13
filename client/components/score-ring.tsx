"use client";

import { useEffect, useId, useState } from "react";

export function ScoreRing({
  score,
  size = 104,
  label = "/ 100",
}: {
  score: number;
  size?: number;
  label?: string;
}) {
  const gradientId = useId();
  const strokeWidth = 9;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const targetOffset = circumference - (Math.max(0, Math.min(100, score)) / 100) * circumference;

  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setOffset(targetOffset));
    return () => cancelAnimationFrame(frame);
  }, [targetOffset]);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--muted)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-1000 ease-out"
        />
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--brand-from)" />
            <stop offset="100%" stopColor="var(--brand-to)" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-semibold tabular-nums">{score}</span>
        <span className="text-[10px] text-muted-foreground">{label}</span>
      </div>
    </div>
  );
}
