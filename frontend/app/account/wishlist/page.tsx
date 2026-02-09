"use client";

import Link from "next/link";
import Image from "next/image";
import { formatPrice, proxyImageUrl } from "@/lib/utils";
import { useWishlist, useRemoveFromWishlist } from "@/hooks/use-wishlist";
import { useAddToCart } from "@/hooks/use-cart";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Heart, ShoppingCart, Trash2 } from "lucide-react";

export default function WishlistPage() {
  const { data: wishlist, isLoading } = useWishlist();
  const removeFromWishlist = useRemoveFromWishlist();
  const addToCart = useAddToCart();

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-64 w-full" />
        ))}
      </div>
    );
  }

  if (!wishlist || wishlist.length === 0) {
    return (
      <div className="text-center py-12">
        <Heart className="h-16 w-16 mx-auto text-primary/40 mb-4" />
        <h2 className="text-xl font-bold mb-2">Your wishlist is empty</h2>
        <p className="text-muted-foreground mb-4">Save products you love for later.</p>
        <Button variant="gradient" size="pill" asChild>
          <Link href="/products">Browse Products</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Wishlist ({wishlist.length})</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {wishlist.map((item) => {
          const img = item.product?.images?.find((i) => i.is_primary) || item.product?.images?.[0];
          return (
            <Card key={item.id} className="overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-primary/10 hover:-translate-y-1 hover:border-primary/20">
              <Link href={`/products/${item.product_id}`}>
                <div className="relative aspect-square bg-muted">
                  {img ? (
                    <Image
                      src={proxyImageUrl(img.url)}
                      alt={item.product?.name || "Product"}
                      fill
                      className="object-cover"
                      sizes="(max-width: 768px) 50vw, 33vw"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-muted-foreground text-sm">
                      No Image
                    </div>
                  )}
                </div>
              </Link>
              <CardContent className="p-3 space-y-2">
                <Link href={`/products/${item.product_id}`}>
                  <h3 className="font-medium text-sm line-clamp-2 hover:text-primary">
                    {item.product?.name}
                  </h3>
                </Link>
                <p className="font-bold">${formatPrice(item.product?.price ?? 0)}</p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    className="flex-1 rounded-full"
                    disabled={!item.product || item.product.stock_quantity <= 0}
                    onClick={() =>
                      addToCart.mutate({ product_id: item.product_id, quantity: 1 })
                    }
                  >
                    <ShoppingCart className="h-3 w-3 mr-1" />
                    Add
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => removeFromWishlist.mutate(item.product_id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
