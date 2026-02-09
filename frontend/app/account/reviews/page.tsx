"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { StarRating } from "@/components/products/star-rating";
import { SentimentBadge } from "@/components/reviews/sentiment-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Star } from "lucide-react";
import type { Review } from "@/types";

export default function MyReviewsPage() {
  const { token } = useAuthStore();
  const { data: reviews, isLoading } = useQuery<Review[]>({
    queryKey: ["user-reviews"],
    queryFn: async () => {
      const res = await api.get("/user/reviews");
      return res.data.data;
    },
    enabled: !!token,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }, (_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  if (!reviews || reviews.length === 0) {
    return (
      <div className="text-center py-12">
        <Star className="h-16 w-16 mx-auto text-primary/40 mb-4" />
        <h2 className="text-xl font-bold mb-2">No reviews yet</h2>
        <p className="text-muted-foreground">Your reviews will appear here after you write them.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">My Reviews ({reviews.length})</h2>
      <div className="space-y-4">
        {reviews.map((review) => (
          <div key={review.id} className="border rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <Link
                href={`/products/${review.product_id}`}
                className="font-medium hover:text-primary"
              >
                {review.product?.name || `Product #${review.product_id}`}
              </Link>
              <SentimentBadge sentiment={review.sentiment} />
            </div>
            <StarRating rating={review.rating} size={14} />
            {review.title && <p className="font-medium text-sm">{review.title}</p>}
            <p className="text-sm text-muted-foreground">{review.comment}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(review.created_at).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
