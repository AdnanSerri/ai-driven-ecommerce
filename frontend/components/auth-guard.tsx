"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { useHydration } from "@/hooks/use-hydration";
import { Skeleton } from "@/components/ui/skeleton";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore();
  const router = useRouter();
  const hydrated = useHydration();

  useEffect(() => {
    // Only redirect after hydration is complete
    if (hydrated && !token) {
      router.push("/login");
    }
  }, [hydrated, token, router]);

  // Show loading skeleton while hydrating
  if (!hydrated) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </div>
    );
  }

  if (!token) return null;

  return <>{children}</>;
}
