"use client";

import { useCategories } from "@/hooks/use-products";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { StarRating } from "@/components/products/star-rating";
import type { ProductFilters, Category } from "@/types";

function getTotalProductsCount(category: Category): number {
  const ownCount = category.products_count ?? 0;
  const childrenCount = category.children?.reduce(
    (sum, child) => sum + getTotalProductsCount(child),
    0
  ) ?? 0;
  return ownCount + childrenCount;
}

interface ProductFiltersProps {
  filters: ProductFilters;
  onFilterChange: (filters: Partial<ProductFilters>) => void;
  onReset: () => void;
}

export function ProductFiltersPanel({ filters, onFilterChange, onReset }: ProductFiltersProps) {
  const { data: categories } = useCategories();

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-semibold mb-3">Categories</h3>
        <div className="space-y-2">
          <button
            onClick={() => onFilterChange({ category_id: undefined })}
            className={`block text-sm w-full text-left px-2 py-1 rounded transition-colors ${
              !filters.category_id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
            }`}
          >
            All Categories
          </button>
          {categories?.map((cat) => {
            const totalProducts = getTotalProductsCount(cat);
            return (
              <button
                key={cat.id}
                onClick={() => onFilterChange({ category_id: cat.id })}
                className={`block text-sm w-full text-left px-2 py-1 rounded transition-colors ${
                  filters.category_id === cat.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
                }`}
              >
                {cat.name}
                <span className="text-xs ml-1 opacity-60">({totalProducts})</span>
              </button>
            );
          })}
        </div>
      </div>

      <Separator />

      <div>
        <h3 className="font-semibold mb-3">Price Range</h3>
        <div className="flex gap-2 items-center">
          <Input
            type="number"
            placeholder="Min"
            value={filters.min_price ?? ""}
            onChange={(e) => onFilterChange({ min_price: e.target.value ? Number(e.target.value) : undefined })}
            className="w-24"
          />
          <span className="text-muted-foreground">-</span>
          <Input
            type="number"
            placeholder="Max"
            value={filters.max_price ?? ""}
            onChange={(e) => onFilterChange({ max_price: e.target.value ? Number(e.target.value) : undefined })}
            className="w-24"
          />
        </div>
      </div>

      <Separator />

      <div>
        <h3 className="font-semibold mb-3">Minimum Rating</h3>
        <StarRating
          rating={filters.min_rating || 0}
          interactive
          onChange={(rating) => onFilterChange({ min_rating: rating })}
          size={20}
        />
        {filters.min_rating && (
          <button
            onClick={() => onFilterChange({ min_rating: undefined })}
            className="text-xs text-muted-foreground mt-1 hover:text-foreground"
          >
            Clear
          </button>
        )}
      </div>

      <Separator />

      <div className="flex items-center gap-2">
        <Checkbox
          id="in-stock"
          checked={filters.in_stock ?? false}
          onCheckedChange={(checked) => onFilterChange({ in_stock: checked ? true : undefined })}
        />
        <Label htmlFor="in-stock" className="text-sm cursor-pointer">
          In Stock Only
        </Label>
      </div>

      <Button variant="outline" size="sm" onClick={onReset} className="w-full rounded-full">
        Reset Filters
      </Button>
    </div>
  );
}
