import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface SessionState {
  viewedProductIds: number[];
  addViewedProduct: (productId: number) => void;
  clearViewedProducts: () => void;
}

const MAX_VIEWED_PRODUCTS = 20;

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      viewedProductIds: [],

      addViewedProduct: (productId: number) =>
        set((state) => {
          // Don't add duplicates, but move to front if already exists
          const filtered = state.viewedProductIds.filter((id) => id !== productId);
          const updated = [productId, ...filtered].slice(0, MAX_VIEWED_PRODUCTS);
          return { viewedProductIds: updated };
        }),

      clearViewedProducts: () => set({ viewedProductIds: [] }),
    }),
    {
      name: "session-storage",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({ viewedProductIds: state.viewedProductIds }),
    }
  )
);
