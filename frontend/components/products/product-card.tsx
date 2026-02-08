"use client";

import Image from "next/image";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StarRating } from "@/components/products/star-rating";
import { StockBadge } from "@/components/products/stock-badge";
import { useAddToCart } from "@/hooks/use-cart";
import { useToggleWishlist, useIsInWishlist } from "@/hooks/use-wishlist";
import { useTrackInteraction } from "@/hooks/use-recommendations";
import { useAuthStore } from "@/stores/auth-store";
import { formatPrice, proxyImageUrl } from "@/lib/utils";
import { Heart, ShoppingCart } from "lucide-react";
import type { Product } from "@/types";

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const addToCart = useAddToCart();
  const toggleWishlist = useToggleWishlist();
  const isInWishlist = useIsInWishlist(product.id);
  const trackInteraction = useTrackInteraction();
  const { token } = useAuthStore();

  const primaryImage = product.images?.find((img) => img.is_primary) || product.images?.[0];

  const handleClick = () => {
    if (token) {
      trackInteraction.mutate({ product_id: product.id, interaction_type: "click" });
    }
  };

  return (
    <Card className="group overflow-hidden transition-shadow hover:shadow-lg">
      <Link href={`/products/${product.id}`} onClick={handleClick}>
        <div className="relative aspect-square overflow-hidden bg-muted">
          {primaryImage ? (
            <Image
              src={proxyImageUrl(primaryImage.url)}
              alt={primaryImage.alt_text || product.name}
              fill
              className="object-cover transition-transform group-hover:scale-105"
              sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              No Image
            </div>
          )}
          {product.compare_at_price && Number(product.compare_at_price) > Number(product.price) && (
            <div className="absolute top-2 left-2 bg-red-500 text-white text-xs px-2 py-1 rounded-md font-medium">
              -{Math.round(((Number(product.compare_at_price) - Number(product.price)) / Number(product.compare_at_price)) * 100)}%
            </div>
          )}
        </div>
      </Link>
      <CardContent className="p-4 space-y-2">
        <Link href={`/products/${product.id}`} onClick={handleClick}>
          <h3 className="font-medium text-sm line-clamp-2 hover:text-primary transition-colors">
            {product.name}
          </h3>
        </Link>
        {product.category && (
          <p className="text-xs text-muted-foreground">{product.category.name}</p>
        )}
        <div className="flex items-center gap-2">
          <StarRating rating={product.average_rating || 0} size={14} />
          {product.reviews_count != null && (
            <span className="text-xs text-muted-foreground">({product.reviews_count})</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="font-bold text-lg">${formatPrice(product.price)}</span>
          {product.compare_at_price && Number(product.compare_at_price) > Number(product.price) && (
            <span className="text-sm text-muted-foreground line-through">
              ${formatPrice(product.compare_at_price)}
            </span>
          )}
        </div>
        <StockBadge quantity={product.stock_quantity} />
        <div className="flex gap-2 pt-2">
          <Button
            size="sm"
            className="flex-1"
            disabled={product.stock_quantity <= 0 || addToCart.isPending || !token}
            onClick={() => addToCart.mutate({ product_id: product.id, quantity: 1 })}
          >
            <ShoppingCart className="h-4 w-4 mr-1" />
            Add
          </Button>
          {token && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => toggleWishlist.mutate(product.id)}
              disabled={toggleWishlist.isPending}
              className={isInWishlist ? "text-red-500 border-red-500 hover:text-red-600 hover:border-red-600" : ""}
            >
              <Heart className={`h-4 w-4 ${isInWishlist ? "fill-current" : ""}`} />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
