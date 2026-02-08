import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { useCartStore } from "@/stores/cart-store";
import type { Cart } from "@/types";

export function useCart() {
  const { token } = useAuthStore();
  const { setItemCount } = useCartStore();

  return useQuery<Cart>({
    queryKey: ["cart"],
    queryFn: async () => {
      const res = await api.get("/cart");
      const cart = res.data.data;
      setItemCount(cart.items_count ?? cart.items?.length ?? 0);
      return cart;
    },
    enabled: !!token,
  });
}

export function useAddToCart() {
  const queryClient = useQueryClient();
  const { increment } = useCartStore();

  return useMutation({
    mutationFn: async (data: { product_id: number; quantity: number }) => {
      const res = await api.post("/cart/items", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      increment();
      toast.success("Added to cart");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to add to cart");
    },
  });
}

export function useUpdateCartItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, quantity }: { id: number; quantity: number }) => {
      const res = await api.put(`/cart/items/${id}`, { quantity });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to update item");
    },
  });
}

export function useRemoveCartItem() {
  const queryClient = useQueryClient();
  const { decrement } = useCartStore();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/cart/items/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      decrement();
      toast.success("Removed from cart");
    },
  });
}

export function useClearCart() {
  const queryClient = useQueryClient();
  const { reset } = useCartStore();

  return useMutation({
    mutationFn: async () => {
      await api.delete("/cart");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      reset();
    },
  });
}
