import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { WishlistItem } from "@/types";

export function useWishlist() {
  const { token } = useAuthStore();

  return useQuery<WishlistItem[]>({
    queryKey: ["wishlist"],
    queryFn: async () => {
      const res = await api.get("/wishlist");
      return res.data.data;
    },
    enabled: !!token,
  });
}

export function useIsInWishlist(productId: number): boolean {
  const { data: wishlist } = useWishlist();
  return wishlist?.some((item) => item.product_id === productId) ?? false;
}

export function useToggleWishlist() {
  const queryClient = useQueryClient();
  const { data: wishlist } = useWishlist();

  return useMutation({
    mutationFn: async (productId: number) => {
      const isInWishlist = wishlist?.some((item) => item.product_id === productId);
      if (isInWishlist) {
        await api.delete(`/wishlist/${productId}`);
        return { action: "removed" };
      } else {
        await api.post("/wishlist", { product_id: productId });
        return { action: "added" };
      }
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      toast.success(result.action === "added" ? "Added to wishlist" : "Removed from wishlist");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to update wishlist");
    },
  });
}

export function useAddToWishlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (product_id: number) => {
      const res = await api.post("/wishlist", { product_id });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      toast.success("Added to wishlist");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to add to wishlist");
    },
  });
}

export function useRemoveFromWishlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (productId: number) => {
      await api.delete(`/wishlist/${productId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      toast.success("Removed from wishlist");
    },
  });
}
