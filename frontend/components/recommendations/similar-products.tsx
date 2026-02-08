"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useSimilarProducts } from "@/hooks/use-products";
import { useRecommendationFeedback } from "@/hooks/use-recommendations";
import { useAuthStore } from "@/stores/auth-store";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { formatPrice, proxyImageUrl, cn } from "@/lib/utils";
import { Package, MoreVertical, X } from "lucide-react";
import type { SimilarProductItem, SimilarProduct } from "@/types";

interface SimilarProductsProps {
  productId: number;
}

function SimilarProductCard({
  product,
  reason,
  onDismiss,
  showDismiss,
}: {
  product: SimilarProductItem;
  reason?: string;
  onDismiss?: (reason?: string) => void;
  showDismiss: boolean;
}) {
  return (
    <Card className="group overflow-hidden transition-shadow hover:shadow-lg relative">
      {/* Dismiss button */}
      {showDismiss && onDismiss && (
        <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="secondary"
                size="icon"
                className="h-7 w-7 rounded-full bg-background/80 backdrop-blur-sm"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
              <DropdownMenuItem onClick={() => onDismiss("not_interested")}>
                <X className="h-4 w-4 mr-2" />
                Not interested
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onDismiss("already_own")}>
                Already own it
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}

      <Link href={`/products/${product.id}`}>
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
        </div>
      </Link>
      <CardContent className="p-4 space-y-2">
        <Link href={`/products/${product.id}`}>
          <h3 className="font-medium text-sm line-clamp-2 hover:text-primary transition-colors">
            {product.name}
          </h3>
        </Link>
        {product.category && (
          <p className="text-xs text-muted-foreground">{product.category}</p>
        )}
        <div className="flex items-center justify-between">
          <span className="font-bold text-lg">${formatPrice(product.price)}</span>
          <span className={`text-xs ${product.in_stock ? "text-green-600" : "text-red-500"}`}>
            {product.in_stock ? "In Stock" : "Out of Stock"}
          </span>
        </div>
        {/* Reason for recommendation */}
        {reason && (
          <p className="text-xs text-muted-foreground line-clamp-1">{reason}</p>
        )}
      </CardContent>
    </Card>
  );
}

export function SimilarProducts({ productId }: SimilarProductsProps) {
  const { token } = useAuthStore();
  const { data: products, isLoading } = useSimilarProducts(productId);
  const feedback = useRecommendationFeedback();
  const [dismissedIds, setDismissedIds] = useState<Set<number>>(new Set());

  const handleDismiss = (productId: number, reason?: string) => {
    setDismissedIds((prev) => new Set([...prev, productId]));
    if (token) {
      feedback.mutate({
        product_id: productId,
        action: "not_interested",
        reason,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Similar Products</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="aspect-square w-full rounded-lg" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-6 w-1/3" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Filter out dismissed products
  const visibleProducts = products?.filter(
    (item) => !dismissedIds.has(item.product.id)
  );

  if (!visibleProducts || visibleProducts.length === 0) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Similar Products</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {visibleProducts.map((item) => (
          <div
            key={item.product.id}
            className={cn(
              "transition-opacity duration-300",
              dismissedIds.has(item.product.id) && "opacity-0 pointer-events-none"
            )}
          >
            <SimilarProductCard
              product={item.product}
              reason="Similar product"
              onDismiss={(reason) => handleDismiss(item.product.id, reason)}
              showDismiss={!!token}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
