import { useAuthStore } from "@/stores/auth-store";

export function getToken(): string | null {
  return useAuthStore.getState().token;
}

export function isAuthenticated(): boolean {
  return !!useAuthStore.getState().token;
}
