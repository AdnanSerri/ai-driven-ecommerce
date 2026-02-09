import { Badge } from "@/components/ui/badge";

interface SentimentBadgeProps {
  sentiment?: "positive" | "negative" | "neutral";
}

export function SentimentBadge({ sentiment }: SentimentBadgeProps) {
  if (!sentiment) return null;

  const variants: Record<string, { variant: "success" | "destructive" | "secondary"; label: string }> = {
    positive: { variant: "success", label: "Positive" },
    negative: { variant: "destructive", label: "Negative" },
    neutral: { variant: "secondary", label: "Neutral" },
  };

  const v = variants[sentiment];
  return (
    <Badge variant={v.variant}>
      {v.label}
    </Badge>
  );
}
