"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StarRating } from "@/components/products/star-rating";
import { StockBadge } from "@/components/products/stock-badge";
import { useAddToCart } from "@/hooks/use-cart";
import { useToggleWishlist, useIsInWishlist } from "@/hooks/use-wishlist";
import { useTrackInteraction } from "@/hooks/use-recommendations";
import { useAuthStore } from "@/stores/auth-store";
import { formatPrice } from "@/lib/utils";
import { Heart, ShoppingCart, Minus, Plus } from "lucide-react";
import type { Product } from "@/types";

interface ProductInfoProps {
  product: Product;
}

export function ProductInfo({ product }: ProductInfoProps) {
  const [quantity, setQuantity] = useState(1);
  const addToCart = useAddToCart();
  const toggleWishlist = useToggleWishlist();
  const isInWishlist = useIsInWishlist(product.id);
  const trackInteraction = useTrackInteraction();
  const { token } = useAuthStore();

  const handleAddToCart = () => {
    addToCart.mutate({ product_id: product.id, quantity });
    if (token) {
      trackInteraction.mutate({ product_id: product.id, interaction_type: "cart_add" });
    }
  };

  const handleWishlist = () => {
    toggleWishlist.mutate(product.id);
    if (token && !isInWishlist) {
      trackInteraction.mutate({ product_id: product.id, interaction_type: "wishlist_add" });
    }
  };

  return (
    <div className="space-y-4">
      {product.category && (
        <div className="text-sm text-muted-foreground">
          <Link href={`/categories/${product.category.id}`} className="hover:text-foreground">
            {product.category.name}
          </Link>
        </div>
      )}

      <h1 className="text-2xl md:text-3xl font-bold">{product.name}</h1>

      <div className="flex items-center gap-3">
        <StarRating rating={product.average_rating || 0} size={20} />
        {product.reviews_count != null && (
          <span className="text-sm text-muted-foreground">
            {product.reviews_count} review{product.reviews_count !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-3">
        <span className="text-3xl font-bold">${formatPrice(product.price)}</span>
        {product.compare_at_price && Number(product.compare_at_price) > Number(product.price) && (
          <span className="text-lg text-muted-foreground line-through">
            ${formatPrice(product.compare_at_price)}
          </span>
        )}
      </div>

      <StockBadge quantity={product.stock_quantity} />

      <p className="text-muted-foreground leading-relaxed">{product.description}</p>

      <div className="flex items-center gap-3 pt-2">
        <div className="flex items-center border rounded-md">
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10 rounded-r-none"
            onClick={() => setQuantity(Math.max(1, quantity - 1))}
          >
            <Minus className="h-4 w-4" />
          </Button>
          <Input
            type="number"
            min={1}
            max={product.stock_quantity}
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, Math.min(product.stock_quantity, Number(e.target.value) || 1)))}
            className="w-16 text-center border-0 rounded-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
          />
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10 rounded-l-none"
            onClick={() => setQuantity(Math.min(product.stock_quantity, quantity + 1))}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        <Button
          size="lg"
          className="flex-1"
          disabled={product.stock_quantity <= 0 || addToCart.isPending || !token}
          onClick={handleAddToCart}
        >
          <ShoppingCart className="h-5 w-5 mr-2" />
          Add to Cart
        </Button>

        {token && (
          <Button
            size="lg"
            variant="outline"
            onClick={handleWishlist}
            disabled={toggleWishlist.isPending}
            className={isInWishlist ? "text-red-500 border-red-500 hover:text-red-600 hover:border-red-600" : ""}
          >
            <Heart className={`h-5 w-5 ${isInWishlist ? "fill-current" : ""}`} />
          </Button>
        )}
      </div>

      <p className="text-xs text-muted-foreground">SKU: {product.sku}</p>
    </div>
  );
}
