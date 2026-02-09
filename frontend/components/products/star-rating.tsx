"use client";

import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface StarRatingProps {
  rating: number;
  maxRating?: number;
  size?: number;
  interactive?: boolean;
  onChange?: (rating: number) => void;
}

export function StarRating({
  rating,
  maxRating = 5,
  size = 16,
  interactive = false,
  onChange,
}: StarRatingProps) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: maxRating }, (_, i) => {
        const filled = i < Math.floor(rating);
        const halfFilled = !filled && i < rating;

        return (
          <button
            key={i}
            type="button"
            disabled={!interactive}
            onClick={() => onChange?.(i + 1)}
            className={cn(
              "p-0 border-0 bg-transparent",
              interactive && "cursor-pointer hover:scale-110 transition-transform"
            )}
          >
            <Star
              size={size}
              className={cn(
                filled
                  ? "fill-warning text-warning"
                  : halfFilled
                  ? "fill-warning/50 text-warning"
                  : "text-muted-foreground/30"
              )}
            />
          </button>
        );
      })}
    </div>
  );
}
