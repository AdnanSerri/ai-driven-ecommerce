"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { StarRating } from "@/components/products/star-rating";
import { SentimentBadge } from "@/components/reviews/sentiment-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { Review } from "@/types";

interface ReviewListProps {
  productId: number;
}

export function ReviewList({ productId }: ReviewListProps) {
  const { data: reviews, isLoading } = useQuery<Review[]>({
    queryKey: ["reviews", productId],
    queryFn: async () => {
      const res = await api.get(`/products/${productId}/reviews`);
      return res.data.data;
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }, (_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  if (!reviews || reviews.length === 0) {
    return <p className="text-muted-foreground text-sm">No reviews yet. Be the first to leave a review!</p>;
  }

  return (
    <div className="space-y-6">
      {reviews.map((review) => (
        <div key={review.id} className="space-y-2 pb-4 border-b last:border-0">
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs">
                {review.user?.name?.charAt(0).toUpperCase() || "U"}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <p className="text-sm font-medium">{review.user?.name || "User"}</p>
              <p className="text-xs text-muted-foreground">
                {new Date(review.created_at).toLocaleDateString()}
              </p>
            </div>
            <SentimentBadge sentiment={review.sentiment} />
          </div>
          <StarRating rating={review.rating} size={14} />
          {review.title && <p className="font-medium text-sm">{review.title}</p>}
          <p className="text-sm text-muted-foreground">{review.comment}</p>
          {review.is_verified_purchase && (
            <p className="text-xs text-green-600 font-medium">Verified Purchase</p>
          )}
        </div>
      ))}
    </div>
  );
}
