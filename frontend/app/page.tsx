"use client";

import Link from "next/link";
import { useProducts, useCategories } from "@/hooks/use-products";
import { useAuthStore } from "@/stores/auth-store";
import { ProductGrid } from "@/components/products/product-grid";
import { RecommendedProducts } from "@/components/recommendations/recommended-products";
import { TrendingProducts } from "@/components/recommendations/trending-products";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowRight, ShoppingBag, TrendingUp } from "lucide-react";
import { Category } from "@/types";

function getTotalProductsCount(category: Category): number {
  const ownCount = category.products_count ?? 0;
  const childrenCount = category.children?.reduce(
    (sum, child) => sum + getTotalProductsCount(child),
    0
  ) ?? 0;
  return ownCount + childrenCount;
}

export default function HomePage() {
  const { token } = useAuthStore();
  const { data: featured, isLoading: featuredLoading } = useProducts({
    sort_by: "created_at",
    sort_order: "desc",
    page: 1,
  });
  const { data: categories, isLoading: categoriesLoading } = useCategories();

  return (
    <div className="space-y-12 pb-12">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary/10 via-background to-primary/5 py-16 md:py-24">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-4">
            Shop Smarter with{" "}
            <span className="text-primary">AI</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
            Discover products tailored to your taste. Our AI-powered platform learns your preferences
            to deliver personalized recommendations.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/products">
                <ShoppingBag className="h-5 w-5 mr-2" />
                Shop Now
              </Link>
            </Button>
            {!token && (
              <Button size="lg" variant="outline" asChild>
                <Link href="/register">Create Account</Link>
              </Button>
            )}
          </div>
        </div>
      </section>

      <div className="container mx-auto px-4 space-y-12">
        {/* Categories */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Shop by Category</h2>
          </div>
          {categoriesLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Array.from({ length: 4 }, (_, i) => (
                <Skeleton key={i} className="h-24 rounded-lg" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {categories?.slice(0, 8).map((cat) => {
                const totalProducts = getTotalProductsCount(cat);
                return (
                  <Link key={cat.id} href={`/categories/${cat.id}`}>
                    <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                      <CardContent className="flex items-center justify-between p-4">
                        <div>
                          <h3 className="font-medium">{cat.name}</h3>
                          <p className="text-xs text-muted-foreground">{totalProducts} products</p>
                        </div>
                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      </CardContent>
                    </Card>
                  </Link>
                );
              })}
            </div>
          )}
        </section>

        {/* Recommendations (for logged-in users) */}
        <RecommendedProducts />

        {/* Trending Products */}
        <TrendingProducts />

        {/* New Arrivals */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              <h2 className="text-2xl font-bold">New Arrivals</h2>
            </div>
            <Button variant="ghost" asChild>
              <Link href="/products?sort_by=created_at&sort_order=desc">
                View All
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </div>
          <ProductGrid
            products={featured?.data.slice(0, 8) || []}
            isLoading={featuredLoading}
          />
        </section>
      </div>
    </div>
  );
}
