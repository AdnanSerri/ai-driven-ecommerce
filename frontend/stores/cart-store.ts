import { create } from "zustand";
import { persist } from "zustand/middleware";

interface CartState {
  itemCount: number;
  setItemCount: (count: number) => void;
  increment: () => void;
  decrement: () => void;
  reset: () => void;
}

export const useCartStore = create<CartState>()(
  persist(
    (set) => ({
      itemCount: 0,
      setItemCount: (count) => set({ itemCount: count }),
      increment: () => set((s) => ({ itemCount: s.itemCount + 1 })),
      decrement: () =>
        set((s) => ({ itemCount: Math.max(0, s.itemCount - 1) })),
      reset: () => set({ itemCount: 0 }),
    }),
    { name: "cart-storage" }
  )
);
