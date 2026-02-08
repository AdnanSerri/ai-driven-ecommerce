"use client";

import { useState } from "react";
import { useRecommendations, useRecommendationFeedback } from "@/hooks/use-recommendations";
import { useAuthStore } from "@/stores/auth-store";
import { ProductCard } from "@/components/products/product-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Sparkles, X, MoreVertical, Eye, User, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

function getReasonStyle(reason: string) {
  const lowerReason = reason.toLowerCase();
  if (lowerReason.includes("viewed")) {
    return { icon: Eye, className: "bg-blue-500 text-white hover:bg-blue-600" };
  }
  if (lowerReason.includes("style") || lowerReason.includes("personality") || lowerReason.includes("shopper")) {
    return { icon: User, className: "bg-purple-500 text-white hover:bg-purple-600" };
  }
  if (lowerReason.includes("recent") || lowerReason.includes("history")) {
    return { icon: Clock, className: "bg-amber-500 text-white hover:bg-amber-600" };
  }
  return { icon: Sparkles, className: "bg-indigo-500 text-white hover:bg-indigo-600" };
}

function ReasonBadge({ reason }: { reason: string }) {
  const { icon: Icon, className } = getReasonStyle(reason);
  return (
    <Badge
      className={cn(
        "flex items-center gap-0 text-xs font-medium border-0 cursor-default transition-all duration-300 ease-out group/badge",
        className
      )}
    >
      <Icon className="h-3 w-3 shrink-0" />
      <span className="max-w-0 overflow-hidden whitespace-nowrap transition-all duration-300 ease-out group-hover/badge:max-w-[300px] group-hover/badge:ml-1">
        {reason}
      </span>
    </Badge>
  );
}

export function RecommendedProducts() {
  const { token } = useAuthStore();
  const { data: recommendations, isLoading } = useRecommendations();
  const feedback = useRecommendationFeedback();
  const [dismissedIds, setDismissedIds] = useState<Set<number>>(new Set());

  const handleDismiss = (productId: number, reason?: string) => {
    setDismissedIds((prev) => new Set([...prev, productId]));
    feedback.mutate({
      product_id: productId,
      action: "not_interested",
      reason,
    });
  };

  if (!token) return null;

  if (isLoading) {
    return (
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          <h2 className="text-xl font-bold">Recommended for You</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="aspect-square w-full rounded-lg" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-6 w-1/3" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  // Filter out dismissed recommendations
  const visibleRecommendations = recommendations?.filter(
    (rec) => !dismissedIds.has(rec.product.id)
  );

  if (!visibleRecommendations || visibleRecommendations.length === 0) return null;

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-primary" />
        <h2 className="text-xl font-bold">Recommended for You</h2>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {visibleRecommendations.map((rec) => (
          <div
            key={rec.product.id}
            className={cn(
              "relative group transition-opacity duration-300",
              dismissedIds.has(rec.product.id) && "opacity-0 pointer-events-none"
            )}
            onMouseEnter={() =>
              feedback.mutate({ product_id: rec.product.id, action: "viewed" })
            }
            onClick={() =>
              feedback.mutate({ product_id: rec.product.id, action: "clicked" })
            }
          >
            {/* Recommendation reason badge - top left */}
            {rec.reason && (
              <div className="absolute top-2 left-2 z-10">
                <ReasonBadge reason={rec.reason} />
              </div>
            )}

            {/* Dismiss button - top right */}
            <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="secondary"
                    size="icon"
                    className="h-7 w-7 rounded-full bg-background/80 backdrop-blur-sm"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
                  <DropdownMenuItem
                    onClick={() => handleDismiss(rec.product.id, "not_interested")}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Not interested
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => handleDismiss(rec.product.id, "already_own")}
                  >
                    Already own it
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => handleDismiss(rec.product.id, "too_expensive")}
                  >
                    Too expensive
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <ProductCard product={rec.product} />
          </div>
        ))}
      </div>
    </section>
  );
}
