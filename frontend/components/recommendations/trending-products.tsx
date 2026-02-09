"use client";

import Image from "next/image";
import Link from "next/link";
import { useTrendingProducts } from "@/hooks/use-recommendations";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatPrice, proxyImageUrl } from "@/lib/utils";
import { Flame, TrendingUp, Package } from "lucide-react";
import type { TrendingProductItem } from "@/types";

interface TrendingProductsProps {
  categoryId?: number;
  limit?: number;
  title?: string;
}

function TrendingProductCard({ product }: { product: TrendingProductItem }) {
  const growthPercent = product.growth_rate
    ? Math.round(product.growth_rate * 100)
    : null;

  return (
    <Card className="group overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-primary/10 hover:-translate-y-1 hover:border-primary/20">
      <Link href={`/products/${product.product_id}`}>
        <div className="relative aspect-square overflow-hidden bg-muted">
          {product.image_url ? (
            <Image
              src={proxyImageUrl(product.image_url)}
              alt={product.name}
              fill
              className="object-cover transition-transform group-hover:scale-105"
              sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <Package className="h-8 w-8 text-muted-foreground" />
            </div>
          )}
          {/* Trending badge */}
          <div className="absolute top-2 left-2">
            <Badge variant="gradient" className="flex items-center gap-1">
              <Flame className="h-3 w-3" />
              Trending
            </Badge>
          </div>
          {/* Growth indicator */}
          {growthPercent !== null && growthPercent > 0 && (
            <div className="absolute top-2 right-2">
              <Badge variant="success" className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                +{growthPercent}%
              </Badge>
            </div>
          )}
        </div>
      </Link>
      <CardContent className="p-4 space-y-2">
        <Link href={`/products/${product.product_id}`}>
          <h3 className="font-medium text-sm line-clamp-2 hover:text-primary transition-colors">
            {product.name}
          </h3>
        </Link>
        {product.category_name && (
          <p className="text-xs text-muted-foreground">{product.category_name}</p>
        )}
        <div className="flex items-center justify-between">
          <span className="font-bold text-lg">
            ${formatPrice(product.price || 0)}
          </span>
          <span
            className={`text-xs ${product.in_stock ? "text-success" : "text-destructive"}`}
          >
            {product.in_stock ? "In Stock" : "Out of Stock"}
          </span>
        </div>
        {/* Activity indicator */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {product.recent_orders > 0 && (
            <span>{product.recent_orders} bought this week</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function TrendingProducts({
  categoryId,
  limit = 8,
  title = "Trending Now",
}: TrendingProductsProps) {
  const { data, isLoading } = useTrendingProducts(categoryId);

  if (isLoading) {
    return (
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Flame className="h-5 w-5 text-warning" />
          <h2 className="text-xl font-bold">{title}</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="aspect-square w-full rounded-lg" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-6 w-1/3" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  const products = data?.products.slice(0, limit) || [];

  if (!products.length) {
    return null;
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2">
        <Flame className="h-5 w-5 text-warning" />
        <h2 className="text-xl font-bold">{title}</h2>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {products.map((product) => (
          <TrendingProductCard key={product.product_id} product={product} />
        ))}
      </div>
    </section>
  );
}
