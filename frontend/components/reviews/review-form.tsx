"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StarRating } from "@/components/products/star-rating";
import { Loader2 } from "lucide-react";

interface ReviewFormProps {
  productId: number;
}

export function ReviewForm({ productId }: ReviewFormProps) {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [rating, setRating] = useState(0);
  const [title, setTitle] = useState("");
  const [comment, setComment] = useState("");

  const submit = useMutation({
    mutationFn: async () => {
      const res = await api.post("/reviews", {
        product_id: productId,
        rating,
        title: title || undefined,
        comment,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews", productId] });
      queryClient.invalidateQueries({ queryKey: ["product", productId] });
      setRating(0);
      setTitle("");
      setComment("");
      toast.success("Review submitted!");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to submit review");
    },
  });

  if (!token) return null;

  return (
    <div className="space-y-4 border rounded-lg p-4">
      <h3 className="font-semibold">Write a Review</h3>
      <div className="space-y-2">
        <Label>Rating</Label>
        <StarRating rating={rating} interactive onChange={setRating} size={24} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="review-title">Title (optional)</Label>
        <Input
          id="review-title"
          placeholder="Summary of your review"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="review-comment">Review</Label>
        <Textarea
          id="review-comment"
          placeholder="What did you think about this product?"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
        />
      </div>
      <Button
        onClick={() => submit.mutate()}
        disabled={rating === 0 || !comment.trim() || submit.isPending}
      >
        {submit.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
        Submit Review
      </Button>
    </div>
  );
}
