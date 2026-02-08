import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { useCartStore } from "@/stores/cart-store";
import type { User } from "@/types";

export function useLogin() {
  const { setAuth } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: async (data: { email: string; password: string }) => {
      const res = await api.post("/login", data);
      return res.data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.token);
      toast.success("Welcome back!");
      router.push("/");
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.message || "Invalid credentials"
      );
    },
  });
}

export function useRegister() {
  const { setAuth } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: async (data: {
      name: string;
      email: string;
      password: string;
      password_confirmation: string;
    }) => {
      const res = await api.post("/register", data);
      return res.data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.token);
      toast.success("Account created successfully!");
      router.push("/");
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.message || "Registration failed"
      );
    },
  });
}

export function useLogout() {
  const { logout } = useAuthStore();
  const { reset } = useCartStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await api.post("/logout");
    },
    onSettled: () => {
      logout();
      reset();
      queryClient.clear();
      router.push("/");
    },
  });
}

export function useProfile() {
  const { token } = useAuthStore();

  return useQuery<User>({
    queryKey: ["profile"],
    queryFn: async () => {
      const res = await api.get("/user/profile");
      return res.data.data;
    },
    enabled: !!token,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();

  return useMutation({
    mutationFn: async (data: Partial<User>) => {
      const res = await api.put("/user/profile", data);
      return res.data.data;
    },
    onSuccess: (user) => {
      setUser(user);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      toast.success("Profile updated");
    },
    onError: () => {
      toast.error("Failed to update profile");
    },
  });
}
