"use client";

import Editor, { loader } from "@monaco-editor/react";

import { useTheme } from "@/lib/theme-context";
import type { CodeLanguage } from "@/lib/types";

// Serve Monaco's own AMD bundle from this app's origin (copied into public/
// by scripts/copy-monaco-assets.js at install time) instead of the default
// jsdelivr CDN - no third-party runtime dependency, and works in restrictive
// network environments.
loader.config({ paths: { vs: "/monaco/vs" } });

export const STARTER_TEMPLATES: Record<CodeLanguage, string> = {
  python:
    "# Write your solution here.\n# Read input with input(), print output with print().\n\n",
  javascript:
    "// Write your solution here.\n" +
    "// Read stdin, then write your solution:\n" +
    "const lines = require('fs').readFileSync('/dev/stdin', 'utf8').split('\\n');\n\n",
  java:
    "import java.util.*;\n\n" +
    "public class Main {\n" +
    "    public static void main(String[] args) {\n" +
    "        Scanner scanner = new Scanner(System.in);\n" +
    "        // Write your solution here.\n" +
    "    }\n" +
    "}\n",
  cpp:
    "#include <bits/stdc++.h>\n" +
    "using namespace std;\n\n" +
    "int main() {\n" +
    "    // Write your solution here.\n" +
    "    return 0;\n" +
    "}\n",
};

const LANGUAGE_OPTIONS: { value: CodeLanguage; label: string; monacoId: string }[] = [
  { value: "python", label: "Python", monacoId: "python" },
  { value: "javascript", label: "JavaScript", monacoId: "javascript" },
  { value: "java", label: "Java", monacoId: "java" },
  { value: "cpp", label: "C++", monacoId: "cpp" },
];

export function CodeEditor({
  language,
  code,
  onLanguageChange,
  onCodeChange,
}: {
  language: CodeLanguage;
  code: string;
  onLanguageChange: (language: CodeLanguage) => void;
  onCodeChange: (code: string) => void;
}) {
  const { theme } = useTheme();
  const monacoId =
    LANGUAGE_OPTIONS.find((option) => option.value === language)?.monacoId ?? "plaintext";

  function handleLanguageChange(next: CodeLanguage) {
    onLanguageChange(next);
    onCodeChange(STARTER_TEMPLATES[next]);
  }

  return (
    <div className="overflow-hidden rounded-xl border border-input">
      <div className="flex items-center justify-between border-b border-input bg-background/60 px-3 py-2">
        <span className="text-xs font-medium text-muted-foreground">Language</span>
        <select
          value={language}
          onChange={(event) => handleLanguageChange(event.target.value as CodeLanguage)}
          className="rounded-lg border border-input bg-background/80 px-2.5 py-1 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          {LANGUAGE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      <Editor
        height="360px"
        language={monacoId}
        theme={theme === "dark" ? "vs-dark" : "vs"}
        value={code}
        onChange={(value) => onCodeChange(value ?? "")}
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          padding: { top: 12 },
        }}
      />
    </div>
  );
}
