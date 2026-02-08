import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { Address } from "@/types";

export function useAddresses() {
  const { token } = useAuthStore();

  return useQuery<Address[]>({
    queryKey: ["addresses"],
    queryFn: async () => {
      const res = await api.get("/addresses");
      return res.data.data;
    },
    enabled: !!token,
  });
}

export function useCreateAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Omit<Address, "id" | "user_id" | "created_at" | "updated_at">) => {
      const res = await api.post("/addresses", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["addresses"] });
      toast.success("Address added");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to add address");
    },
  });
}

export function useUpdateAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...data }: Partial<Address> & { id: number }) => {
      const res = await api.put(`/addresses/${id}`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["addresses"] });
      toast.success("Address updated");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to update address");
    },
  });
}

export function useDeleteAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/addresses/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["addresses"] });
      toast.success("Address removed");
    },
  });
}

export function useSetDefaultAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/addresses/${id}/default`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["addresses"] });
      toast.success("Default address updated");
    },
  });
}
