import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { useSessionStore } from "@/stores/session-store";
import { useFilterContextStore } from "@/stores/filter-context-store";
import type {
  Recommendation,
  PersonalityProfile,
  PersonalityTraits,
  FrequentlyBoughtTogetherResponse,
  TrendingProductsResponse,
} from "@/types";

export function useRecommendations() {
  const { token } = useAuthStore();
  const { viewedProductIds } = useSessionStore();

  return useQuery<Recommendation[]>({
    queryKey: ["recommendations", viewedProductIds.slice(0, 10).join(",")],
    queryFn: async () => {
      const sessionParam = viewedProductIds.length > 0
        ? `?session_product_ids=${viewedProductIds.slice(0, 10).join(",")}`
        : "";
      const res = await api.get(`/recommendations${sessionParam}`);
      return res.data.data;
    },
    enabled: !!token,
    staleTime: 1000 * 30, // 30 seconds - recommendations should update frequently
    gcTime: 1000 * 60, // 1 minute garbage collection
  });
}

export function useFrequentlyBoughtTogether(productId: number) {
  return useQuery<FrequentlyBoughtTogetherResponse>({
    queryKey: ["frequently-bought-together", productId],
    queryFn: async () => {
      const res = await api.get(`/recommendations/bought-together/${productId}`);
      return res.data;
    },
    enabled: !!productId,
    staleTime: 1000 * 60 * 60, // 1 hour - these don't change often
  });
}

export function useTrendingProducts(categoryId?: number) {
  return useQuery<TrendingProductsResponse>({
    queryKey: ["trending-products", categoryId],
    queryFn: async () => {
      const params = categoryId ? `?category_id=${categoryId}` : "";
      const res = await api.get(`/recommendations/trending${params}`);
      return res.data;
    },
    staleTime: 1000 * 60 * 15, // 15 minutes
  });
}

export function usePersonalityProfile() {
  const { token } = useAuthStore();

  return useQuery<PersonalityProfile>({
    queryKey: ["personality"],
    queryFn: async () => {
      const res = await api.get("/user/personality");
      return res.data.data;
    },
    enabled: !!token,
    staleTime: 1000 * 60 * 2, // 2 minutes - personality changes less frequently
  });
}

export function useRefreshPersonality() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const res = await api.get("/user/personality?refresh=true");
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["personality"] });
      queryClient.invalidateQueries({ queryKey: ["personality-traits"] });
    },
  });
}

export function usePersonalityTraits() {
  const { token } = useAuthStore();

  return useQuery<PersonalityTraits>({
    queryKey: ["personality-traits"],
    queryFn: async () => {
      const res = await api.get("/user/personality/traits");
      return res.data.data;
    },
    enabled: !!token,
    staleTime: 1000 * 60 * 2, // 2 minutes - personality changes less frequently
  });
}

export function useTrackInteraction() {
  const queryClient = useQueryClient();
  const { addViewedProduct } = useSessionStore();
  const { getFilterContext } = useFilterContextStore();

  return useMutation({
    mutationFn: async (data: {
      product_id: number;
      interaction_type: "view" | "click" | "cart_add" | "wishlist_add" | "purchase";
      metadata?: Record<string, unknown>;
    }) => {
      // Track in session store for session-based recommendations
      if (data.interaction_type === "view") {
        addViewedProduct(data.product_id);
      }

      // Include filter context for click interactions
      let metadata = data.metadata || {};
      if (data.interaction_type === "click") {
        const filterContext = getFilterContext();
        if (filterContext) {
          metadata = {
            ...metadata,
            filter_context: filterContext,
          };
        }
      }

      await api.post("/interactions", {
        product_id: data.product_id,
        interaction_type: data.interaction_type,
        ...(Object.keys(metadata).length > 0 && { metadata }),
      });

      return data.interaction_type;
    },
    onSuccess: (interactionType) => {
      // Invalidate recommendations cache on significant interactions
      if (["view", "click", "purchase", "cart_add", "wishlist_add"].includes(interactionType)) {
        queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      }
      // Invalidate personality on purchase (most significant signal)
      if (interactionType === "purchase") {
        queryClient.invalidateQueries({ queryKey: ["personality"] });
        queryClient.invalidateQueries({ queryKey: ["personality-traits"] });
      }
    },
  });
}

export function useRecommendationFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      product_id: number;
      action: "clicked" | "viewed" | "dismissed" | "not_interested";
      reason?: string;
    }) => {
      if (data.action === "not_interested") {
        // Call the not-interested endpoint
        await api.post("/recommendations/not-interested", {}, {
          params: {
            product_id: data.product_id,
            reason: data.reason,
          },
        });
      } else {
        await api.post("/recommendations/feedback", data);
      }
    },
    onSuccess: (_, variables) => {
      // Invalidate recommendations if user marked something as not interested
      if (variables.action === "not_interested" || variables.action === "dismissed") {
        queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      }
    },
  });
}

export function useRemoveNotInterested() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (productId: number) => {
      await api.delete("/recommendations/not-interested", {
        params: { product_id: productId },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}
