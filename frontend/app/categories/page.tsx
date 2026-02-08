"use client";

import Link from "next/link";
import { useCategories } from "@/hooks/use-products";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Grid3X3, ChevronRight } from "lucide-react";
import { Category } from "@/types";

function getTotalProductsCount(category: Category): number {
  const ownCount = category.products_count ?? 0;
  const childrenCount = category.children?.reduce(
    (sum, child) => sum + getTotalProductsCount(child),
    0
  ) ?? 0;
  return ownCount + childrenCount;
}

export default function CategoriesPage() {
  const { data: categories, isLoading } = useCategories();

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="space-y-6">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i}>
              <Skeleton className="h-8 w-48 mb-3" />
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {Array.from({ length: 4 }, (_, j) => (
                  <Skeleton key={j} className="h-24 w-full rounded-lg" />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Categories</h1>

      {categories && categories.length > 0 ? (
        <div className="space-y-8">
          {categories.map((category) => {
            const totalProducts = getTotalProductsCount(category);
            const hasChildren = category.children && category.children.length > 0;

            return (
              <div key={category.id} className="space-y-4">
                <div className="flex items-center justify-between">
                  <Link
                    href={`/categories/${category.id}`}
                    className="group flex items-center gap-2 hover:text-primary transition-colors"
                  >
                    <Grid3X3 className="h-6 w-6 text-primary" />
                    <h2 className="text-xl font-semibold">{category.name}</h2>
                    <ChevronRight className="h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Link>
                  <span className="text-sm text-muted-foreground">
                    {totalProducts} product{totalProducts !== 1 ? "s" : ""}
                  </span>
                </div>

                {hasChildren ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {category.children!.map((child) => (
                      <Link key={child.id} href={`/categories/${child.id}`}>
                        <Card className="h-full hover:shadow-md transition-shadow cursor-pointer">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-base">
                              {child.name}
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="pt-0">
                            {child.products_count != null && (
                              <p className="text-sm text-muted-foreground">
                                {child.products_count} product{child.products_count !== 1 ? "s" : ""}
                              </p>
                            )}
                          </CardContent>
                        </Card>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <Link href={`/categories/${category.id}`}>
                    <Card className="hover:shadow-md transition-shadow cursor-pointer max-w-sm">
                      <CardContent className="py-4">
                        <p className="text-sm text-muted-foreground">
                          Browse {category.name}
                        </p>
                      </CardContent>
                    </Card>
                  </Link>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <Grid3X3 className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">No categories found</p>
        </div>
      )}
    </div>
  );
}
