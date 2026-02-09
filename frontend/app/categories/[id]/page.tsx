"use client";

import { use, useState } from "react";
import { useProducts, useCategories } from "@/hooks/use-products";
import { ProductGrid } from "@/components/products/product-grid";
import { ProductSort } from "@/components/products/product-sort";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ProductFilters, Category } from "@/types";

function findCategoryById(categories: Category[], id: number): Category | undefined {
  for (const cat of categories) {
    if (cat.id === id) return cat;
    if (cat.children) {
      const found = findCategoryById(cat.children, id);
      if (found) return found;
    }
  }
  return undefined;
}

export default function CategoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const categoryId = Number(id);

  const [filters, setFilters] = useState<ProductFilters>({
    category_id: categoryId,
    sort_by: "created_at",
    sort_order: "desc",
    page: 1,
  });

  const { data, isLoading } = useProducts(filters);
  const { data: categories } = useCategories();
  const category = categories ? findCategoryById(categories, categoryId) : undefined;

  const handleSortChange = (value: string) => {
    const [sort_by, sort_order] = value.split(":") as [ProductFilters["sort_by"], ProductFilters["sort_order"]];
    setFilters((prev) => ({ ...prev, sort_by, sort_order, page: 1 }));
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{category?.name || "Category"}</h1>
          {category?.description && (
            <p className="text-muted-foreground mt-1">{category.description}</p>
          )}
        </div>
        <ProductSort
          value={`${filters.sort_by || "created_at"}:${filters.sort_order || "desc"}`}
          onChange={handleSortChange}
        />
      </div>

      {data && (
        <p className="text-sm text-muted-foreground mb-4">
          {data.total} product{data.total !== 1 ? "s" : ""}
        </p>
      )}

      <ProductGrid products={data?.data || []} isLoading={isLoading} />

      {data && data.last_page > 1 && (
        <div className="flex items-center justify-center gap-2 pt-6">
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
  );
}
