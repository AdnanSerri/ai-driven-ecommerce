"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { useFrequentlyBoughtTogether } from "@/hooks/use-recommendations";
import { useAddToCart } from "@/hooks/use-cart";
import { useAuthStore } from "@/stores/auth-store";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { formatPrice, proxyImageUrl } from "@/lib/utils";
import { ShoppingCart, Package, Plus } from "lucide-react";
import type { FrequentlyBoughtTogetherItem } from "@/types";

interface FrequentlyBoughtTogetherProps {
  productId: number;
  currentProductName: string;
  currentProductPrice: number;
  currentProductImage?: string;
}

function ProductItem({
  product,
  selected,
  onSelect,
}: {
  product: FrequentlyBoughtTogetherItem;
  selected: boolean;
  onSelect: (selected: boolean) => void;
}) {
  return (
    <div className="flex items-center gap-3 p-3 border rounded-lg bg-background">
      <Checkbox
        checked={selected}
        onCheckedChange={onSelect}
        disabled={!product.in_stock}
      />
      <Link href={`/products/${product.product_id}`} className="shrink-0">
        <div className="relative w-16 h-16 rounded overflow-hidden bg-muted">
          {product.image_url ? (
            <Image
              src={proxyImageUrl(product.image_url)}
              alt={product.name}
              fill
              className="object-cover"
              sizes="64px"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <Package className="h-6 w-6 text-muted-foreground" />
            </div>
          )}
        </div>
      </Link>
      <div className="flex-1 min-w-0">
        <Link
          href={`/products/${product.product_id}`}
          className="text-sm font-medium hover:text-primary line-clamp-2"
        >
          {product.name}
        </Link>
        <div className="flex items-center gap-2 mt-1">
          <span className="font-bold">
            ${formatPrice(product.price || 0)}
          </span>
          {!product.in_stock && (
            <span className="text-xs text-destructive">Out of stock</span>
          )}
        </div>
      </div>
    </div>
  );
}

export function FrequentlyBoughtTogether({
  productId,
  currentProductName,
  currentProductPrice,
  currentProductImage,
}: FrequentlyBoughtTogetherProps) {
  const { token } = useAuthStore();
  const { data, isLoading } = useFrequentlyBoughtTogether(productId);
  const addToCartMutation = useAddToCart();
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Initialize selection when data loads
  const products = data?.products || [];

  const handleSelectAll = () => {
    if (selectedIds.size === products.filter((p) => p.in_stock).length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(products.filter((p) => p.in_stock).map((p) => p.product_id)));
    }
  };

  const handleSelect = (productId: number, selected: boolean) => {
    const newSelected = new Set(selectedIds);
    if (selected) {
      newSelected.add(productId);
    } else {
      newSelected.delete(productId);
    }
    setSelectedIds(newSelected);
  };

  const handleAddAllToCart = async () => {
    if (!token) return;

    // Add selected products to cart
    for (const pid of selectedIds) {
      await addToCartMutation.mutateAsync({ product_id: pid, quantity: 1 });
    }
  };

  // Calculate bundle total
  const bundleTotal =
    currentProductPrice +
    products
      .filter((p) => selectedIds.has(p.product_id))
      .reduce((sum, p) => sum + (p.price || 0), 0);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Frequently Bought Together</h3>
        </div>
        <div className="grid gap-3">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (!products.length) {
    return null;
  }

  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-5 w-5 text-primary" />
            <h3 className="text-lg font-semibold">Frequently Bought Together</h3>
          </div>
          {products.filter((p) => p.in_stock).length > 0 && (
            <Button variant="ghost" size="sm" onClick={handleSelectAll}>
              {selectedIds.size === products.filter((p) => p.in_stock).length
                ? "Deselect All"
                : "Select All"}
            </Button>
          )}
        </div>

        {/* Current product */}
        <div className="flex items-center gap-3 p-3 border-2 border-primary/20 rounded-lg bg-primary/5">
          <div className="relative w-16 h-16 rounded overflow-hidden bg-muted shrink-0">
            {currentProductImage ? (
              <Image
                src={proxyImageUrl(currentProductImage)}
                alt={currentProductName}
                fill
                className="object-cover"
                sizes="64px"
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <Package className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium line-clamp-2">{currentProductName}</p>
            <p className="font-bold mt-1">${formatPrice(currentProductPrice)}</p>
          </div>
          <span className="text-xs text-muted-foreground">This item</span>
        </div>

        {/* Plus icon */}
        <div className="flex justify-center">
          <Plus className="h-5 w-5 text-muted-foreground" />
        </div>

        {/* Co-purchased products */}
        <div className="space-y-3">
          {products.map((product) => (
            <ProductItem
              key={product.product_id}
              product={product}
              selected={selectedIds.has(product.product_id)}
              onSelect={(selected) => handleSelect(product.product_id, selected)}
            />
          ))}
        </div>

        {/* Bundle total and add to cart */}
        {token && selectedIds.size > 0 && (
          <div className="pt-4 border-t space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Bundle total ({selectedIds.size + 1} items):
              </span>
              <span className="text-xl font-bold">${formatPrice(bundleTotal)}</span>
            </div>
            <Button
              variant="gradient"
              className="w-full rounded-full"
              onClick={handleAddAllToCart}
              disabled={addToCartMutation.isPending}
            >
              <ShoppingCart className="h-4 w-4 mr-2" />
              Add Selected to Cart
            </Button>
          </div>
        )}

        {!token && (
          <p className="text-sm text-muted-foreground text-center pt-2">
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>{" "}
            to add items to cart
          </p>
        )}
      </CardContent>
    </Card>
  );
}
