import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { useCartStore } from "@/stores/cart-store";
import type { Order, PaginatedResponse } from "@/types";

export function useOrders(page = 1) {
  const { token } = useAuthStore();

  return useQuery<PaginatedResponse<Order>>({
    queryKey: ["orders", page],
    queryFn: async () => {
      const res = await api.get(`/orders?page=${page}`);
      return res.data;
    },
    enabled: !!token,
  });
}

export function useOrder(id: number) {
  const { token } = useAuthStore();

  return useQuery<Order>({
    queryKey: ["order", id],
    queryFn: async () => {
      const res = await api.get(`/orders/${id}`);
      return res.data.data;
    },
    enabled: !!token && !!id,
  });
}

export function useCheckout() {
  const queryClient = useQueryClient();
  const { reset } = useCartStore();
  const router = useRouter();

  return useMutation({
    mutationFn: async (data: {
      shipping_address_id: number;
      billing_address_id: number;
      notes?: string;
    }) => {
      const res = await api.post("/checkout", data);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      reset();
      toast.success(`Order #${data.data?.order_number || ""} placed!`);
      router.push(`/account/orders/${data.data?.id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Checkout failed");
    },
  });
}

export function useCancelOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const res = await api.post(`/orders/${id}/cancel`);
      return res.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["order", id] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      toast.success("Order cancelled");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to cancel order");
    },
  });
}
