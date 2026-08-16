import { CheckCircle2, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { ExecutionResult } from "@/lib/types";

export function TestCaseResults({ results }: { results: ExecutionResult[] }) {
  const passedCount = results.filter((result) => result.passed).length;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Test results</h3>
        <Badge variant={passedCount === results.length ? "success" : "destructive"}>
          {passedCount}/{results.length} passed
        </Badge>
      </div>
      <div className="flex flex-col gap-2">
        {results.map((result, index) => (
          <div
            key={index}
            className="rounded-xl border border-border bg-background/40 p-3 text-sm"
          >
            <div className="mb-2 flex items-center gap-2">
              {result.passed ? (
                <CheckCircle2 className="size-4 shrink-0 text-emerald-500" />
              ) : (
                <XCircle className="size-4 shrink-0 text-destructive" />
              )}
              <span className="font-medium">Test case {index + 1}</span>
            </div>
            <div className="grid gap-1.5 pl-6 text-muted-foreground">
              {result.input && (
                <div>
                  <span className="font-medium text-foreground">Input: </span>
                  <code className="break-all">{result.input}</code>
                </div>
              )}
              <div>
                <span className="font-medium text-foreground">Expected: </span>
                <code className="break-all">{result.expected_output}</code>
              </div>
              <div>
                <span className="font-medium text-foreground">Got: </span>
                <code className="break-all">{result.actual_output || "(no output)"}</code>
              </div>
              {result.stderr && (
                <div className="text-destructive">
                  <span className="font-medium">Error: </span>
                  <code className="break-all">{result.stderr}</code>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
