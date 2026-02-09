"use client";

import { Suspense, useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useProducts } from "@/hooks/use-products";
import { ProductGrid } from "@/components/products/product-grid";
import { ProductFiltersPanel } from "@/components/products/product-filters";
import { ProductSort } from "@/components/products/product-sort";
import { SearchBar } from "@/components/layout/search-bar";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { SlidersHorizontal, ChevronLeft, ChevronRight } from "lucide-react";
import { useFilterContextStore } from "@/stores/filter-context-store";
import type { ProductFilters } from "@/types";

export default function ProductsPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-6">
          <Skeleton className="h-8 w-32 mb-6" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }, (_, i) => (
              <div key={i} className="space-y-3">
                <Skeleton className="aspect-square w-full rounded-lg" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-6 w-1/3" />
              </div>
            ))}
          </div>
        </div>
      }
    >
      <ProductsContent />
    </Suspense>
  );
}

function ProductsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { setActiveFilters, clearFilters } = useFilterContextStore();
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const [filters, setFilters] = useState<ProductFilters>({
    search: searchParams.get("search") || undefined,
    category_id: searchParams.get("category_id") ? Number(searchParams.get("category_id")) : undefined,
    min_price: searchParams.get("min_price") ? Number(searchParams.get("min_price")) : undefined,
    max_price: searchParams.get("max_price") ? Number(searchParams.get("max_price")) : undefined,
    min_rating: searchParams.get("min_rating") ? Number(searchParams.get("min_rating")) : undefined,
    in_stock: searchParams.get("in_stock") === "1" ? true : undefined,
    sort_by: (searchParams.get("sort_by") as ProductFilters["sort_by"]) || "created_at",
    sort_order: (searchParams.get("sort_order") as ProductFilters["sort_order"]) || "desc",
    page: searchParams.get("page") ? Number(searchParams.get("page")) : 1,
  });

  const { data, isLoading } = useProducts(filters);

  // Sync filters to URL
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.search) params.set("search", filters.search);
    if (filters.category_id) params.set("category_id", String(filters.category_id));
    if (filters.min_price != null) params.set("min_price", String(filters.min_price));
    if (filters.max_price != null) params.set("max_price", String(filters.max_price));
    if (filters.min_rating != null) params.set("min_rating", String(filters.min_rating));
    if (filters.in_stock) params.set("in_stock", "1");
    if (filters.sort_by && filters.sort_by !== "created_at") params.set("sort_by", filters.sort_by);
    if (filters.sort_order && filters.sort_order !== "desc") params.set("sort_order", filters.sort_order);
    if (filters.page && filters.page > 1) params.set("page", String(filters.page));
    router.replace(`/products?${params.toString()}`, { scroll: false });
  }, [filters, router]);

  // Sync filters to context store with debounce (500ms) for tracking
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      setActiveFilters(filters);
    }, 500);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [filters, setActiveFilters]);

  // Clear filter context on unmount
  useEffect(() => {
    return () => {
      clearFilters();
    };
  }, [clearFilters]);

  const handleFilterChange = (partial: Partial<ProductFilters>) => {
    setFilters((prev) => ({ ...prev, ...partial, page: 1 }));
  };

  const handleSortChange = (value: string) => {
    const [sort_by, sort_order] = value.split(":") as [ProductFilters["sort_by"], ProductFilters["sort_order"]];
    setFilters((prev) => ({ ...prev, sort_by, sort_order, page: 1 }));
  };

  const handleReset = () => {
    setFilters({ sort_by: "created_at", sort_order: "desc", page: 1 });
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Products</h1>
        <div className="flex items-center gap-3">
          <div className="hidden md:block">
            <ProductSort
              value={`${filters.sort_by || "created_at"}:${filters.sort_order || "desc"}`}
              onChange={handleSortChange}
            />
          </div>
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" className="md:hidden">
                <SlidersHorizontal className="h-4 w-4 mr-2" />
                Filters
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-80 overflow-y-auto">
              <SheetTitle className="mb-4">Filters</SheetTitle>
              <ProductSort
                value={`${filters.sort_by || "created_at"}:${filters.sort_order || "desc"}`}
                onChange={handleSortChange}
              />
              <div className="mt-4">
                <ProductFiltersPanel filters={filters} onFilterChange={handleFilterChange} onReset={handleReset} />
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>

      <div className="md:hidden mb-4">
        <SearchBar />
      </div>

      <div className="flex gap-8">
        <aside className="hidden md:block w-64 flex-shrink-0">
          <div className="border rounded-xl bg-card/50 p-4">
            <ProductFiltersPanel filters={filters} onFilterChange={handleFilterChange} onReset={handleReset} />
          </div>
        </aside>

        <div className="flex-1 space-y-6">
          {data && (
            <p className="text-sm text-muted-foreground">
              Showing {data.from}–{data.to} of {data.total} products
            </p>
          )}

          <ProductGrid products={data?.data || []} isLoading={isLoading} />

          {data && data.last_page > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <Button
                variant="outline"
                size="sm"
                className="rounded-full"
                disabled={data.current_page <= 1}
                onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) - 1 }))}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <span className="text-sm text-muted-foreground px-4">
                Page {data.current_page} of {data.last_page}
              </span>
              <Button
                variant="outline"
                size="sm"
                className="rounded-full"
                disabled={data.current_page >= data.last_page}
                onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
