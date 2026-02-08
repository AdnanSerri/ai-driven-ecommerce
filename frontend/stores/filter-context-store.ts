import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ProductFilters } from "@/types";

/**
 * Filter context for tracking active filters when users interact with products.
 * This context is included in interaction tracking to improve personalization.
 */
export interface FilterContext {
  category_id?: number;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  in_stock?: boolean;
  applied_at: number; // timestamp
}

interface FilterContextState {
  activeFilters: FilterContext | null;
  filtersAppliedAt: number | null;

  /**
   * Update active filters from the products page.
   * Only stores meaningful filters (ignores defaults like sort_by).
   */
  setActiveFilters: (filters: ProductFilters) => void;

  /**
   * Get filter context for tracking, if filters were applied recently (within 5 min).
   */
  getFilterContext: () => FilterContext | null;

  /**
   * Clear the filter context.
   */
  clearFilters: () => void;
}

const FILTER_CONTEXT_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

/**
 * Check if any meaningful filters are applied.
 * Ignores pagination, sorting, and search (search is handled separately).
 */
function hasMeaningfulFilters(filters: ProductFilters): boolean {
  return !!(
    filters.category_id ||
    filters.min_price != null ||
    filters.max_price != null ||
    filters.min_rating != null ||
    filters.in_stock
  );
}

/**
 * Extract only the meaningful filter values for tracking.
 */
function extractFilterContext(filters: ProductFilters): FilterContext {
  return {
    category_id: filters.category_id,
    min_price: filters.min_price,
    max_price: filters.max_price,
    min_rating: filters.min_rating,
    in_stock: filters.in_stock,
    applied_at: Date.now(),
  };
}

export const useFilterContextStore = create<FilterContextState>()(
  persist(
    (set, get) => ({
      activeFilters: null,
      filtersAppliedAt: null,

      setActiveFilters: (filters: ProductFilters) => {
        if (hasMeaningfulFilters(filters)) {
          const context = extractFilterContext(filters);
          set({
            activeFilters: context,
            filtersAppliedAt: context.applied_at,
          });
        } else {
          // Clear if no meaningful filters
          set({
            activeFilters: null,
            filtersAppliedAt: null,
          });
        }
      },

      getFilterContext: () => {
        const state = get();
        if (!state.activeFilters || !state.filtersAppliedAt) {
          return null;
        }

        // Check if filters are still within TTL (5 minutes)
        const elapsed = Date.now() - state.filtersAppliedAt;
        if (elapsed > FILTER_CONTEXT_TTL) {
          return null;
        }

        return state.activeFilters;
      },

      clearFilters: () =>
        set({
          activeFilters: null,
          filtersAppliedAt: null,
        }),
    }),
    {
      name: "filter-context-storage",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        activeFilters: state.activeFilters,
        filtersAppliedAt: state.filtersAppliedAt,
      }),
    }
  )
);
