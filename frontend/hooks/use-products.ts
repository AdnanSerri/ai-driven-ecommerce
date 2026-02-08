import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Product, Category, PaginatedResponse, ProductFilters, SimilarProduct } from "@/types";

export function useProducts(filters: ProductFilters) {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  // Backend expects 'category' not 'category_id'
  if (filters.category_id) params.set("category", String(filters.category_id));
  if (filters.min_price != null) params.set("min_price", String(filters.min_price));
  if (filters.max_price != null) params.set("max_price", String(filters.max_price));
  if (filters.min_rating != null) params.set("min_rating", String(filters.min_rating));
  if (filters.in_stock != null) params.set("in_stock", filters.in_stock ? "1" : "0");
  // Map sort_by values to backend expected values
  if (filters.sort_by) {
    const sortByMap: Record<string, string> = {
      stock_quantity: "stock",
      created_at: "created_at",
      price: "price",
      name: "name",
    };
    params.set("sort_by", sortByMap[filters.sort_by] || filters.sort_by);
  }
  // Backend expects 'sort_dir' not 'sort_order'
  if (filters.sort_order) params.set("sort_dir", filters.sort_order);
  if (filters.page) params.set("page", String(filters.page));

  return useQuery<PaginatedResponse<Product>>({
    queryKey: ["products", filters],
    queryFn: async () => {
      const res = await api.get(`/products?${params.toString()}`);
      // Backend returns { data, links, meta } structure
      // Transform to flat structure expected by frontend
      const { data, meta } = res.data;
      return {
        data,
        current_page: meta.current_page,
        last_page: meta.last_page,
        per_page: meta.per_page,
        total: meta.total,
        from: meta.from || 0,
        to: meta.to || 0,
      };
    },
  });
}

export function useProduct(id: number) {
  return useQuery<Product>({
    queryKey: ["product", id],
    queryFn: async () => {
      const res = await api.get(`/products/${id}`);
      return res.data.data;
    },
    enabled: !!id,
  });
}

export function useCategories() {
  return useQuery<Category[]>({
    queryKey: ["categories"],
    queryFn: async () => {
      const res = await api.get("/categories");
      return res.data.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useSimilarProducts(productId: number) {
  return useQuery<SimilarProduct[]>({
    queryKey: ["similar-products", productId],
    queryFn: async () => {
      const res = await api.get(`/products/${productId}/similar`);
      return res.data.data;
    },
    enabled: !!productId,
  });
}
