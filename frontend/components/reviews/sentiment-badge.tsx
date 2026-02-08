import { Badge } from "@/components/ui/badge";

interface SentimentBadgeProps {
  sentiment?: "positive" | "negative" | "neutral";
}

export function SentimentBadge({ sentiment }: SentimentBadgeProps) {
  if (!sentiment) return null;

  const variants: Record<string, { className: string; label: string }> = {
    positive: { className: "bg-green-100 text-green-700", label: "Positive" },
    negative: { className: "bg-red-100 text-red-700", label: "Negative" },
    neutral: { className: "bg-gray-100 text-gray-700", label: "Neutral" },
  };

  const v = variants[sentiment];
  return (
    <Badge variant="secondary" className={v.className}>
      {v.label}
    </Badge>
  );
}
