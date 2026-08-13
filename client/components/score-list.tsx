import { AlertTriangle, CheckCircle2, Lightbulb } from "lucide-react";

const LIST_STYLES = {
  positive: { icon: CheckCircle2, color: "text-emerald-500" },
  negative: { icon: AlertTriangle, color: "text-amber-500" },
  suggestion: { icon: Lightbulb, color: "text-[var(--brand-via)]" },
} as const;

export function ScoreList({
  title,
  items,
  kind,
}: {
  title: string;
  items: string[];
  kind: keyof typeof LIST_STYLES;
}) {
  if (items.length === 0) return null;

  const { icon: Icon, color } = LIST_STYLES[kind];

  return (
    <div>
      <h3 className="mb-2 text-sm font-medium">{title}</h3>
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li
            key={index}
            className="flex items-start gap-2 text-sm text-muted-foreground"
          >
            <Icon className={`mt-0.5 size-4 shrink-0 ${color}`} />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
