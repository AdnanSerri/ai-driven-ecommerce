"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { useAuthStore } from "@/stores/auth-store";
import { useHydration } from "@/hooks/use-hydration";

function AuthCookieSync() {
  const token = useAuthStore((s) => s.token);
  const hydrated = useHydration();

  useEffect(() => {
    // Only sync cookie after hydration to avoid clearing valid tokens
    if (!hydrated) return;

    if (token) {
      document.cookie = `auth-token=${token}; path=/; SameSite=Lax`;
    } else {
      document.cookie = "auth-token=; path=/; max-age=0";
    }
  }, [hydrated, token]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthCookieSync />
      {children}
      <Toaster position="bottom-right" richColors />
    </QueryClientProvider>
  );
}
