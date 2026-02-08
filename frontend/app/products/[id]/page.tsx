"use client";

import { use, useEffect } from "react";
import { useProduct } from "@/hooks/use-products";
import { useTrackInteraction } from "@/hooks/use-recommendations";
import { useAuthStore } from "@/stores/auth-store";
import { ProductImages } from "@/components/products/product-images";
import { ProductInfo } from "@/components/products/product-info";
import { ReviewList } from "@/components/reviews/review-list";
import { ReviewForm } from "@/components/reviews/review-form";
import { SimilarProducts } from "@/components/recommendations/similar-products";
import { FrequentlyBoughtTogether } from "@/components/recommendations/frequently-bought-together";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

export default function ProductDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const productId = Number(id);
  const { data: product, isLoading } = useProduct(productId);
  const trackInteraction = useTrackInteraction();
  const { token } = useAuthStore();

  useEffect(() => {
    // Only track interactions for logged-in users
    if (productId && token) {
      trackInteraction.mutate({ product_id: productId, interaction_type: "view" });
    }
  }, [productId, token]);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <div className="grid md:grid-cols-2 gap-8">
          <Skeleton className="aspect-square w-full rounded-lg" />
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-10 w-1/3" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <h1 className="text-2xl font-bold">Product not found</h1>
        <p className="text-muted-foreground mt-2">The product you&apos;re looking for doesn&apos;t exist.</p>
      </div>
    );
  }

  // Get primary image URL
  const primaryImage = product.images?.find((img) => img.is_primary)?.url || product.images?.[0]?.url;

  return (
    <div className="container mx-auto px-4 py-6 space-y-10">
      <div className="grid md:grid-cols-2 gap-8">
        <ProductImages images={product.images} productName={product.name} />
        <div className="space-y-6">
          <ProductInfo product={product} />

          {/* Frequently Bought Together - below product info */}
          <FrequentlyBoughtTogether
            productId={productId}
            currentProductName={product.name}
            currentProductPrice={product.price}
            currentProductImage={primaryImage}
          />
        </div>
      </div>

      <Separator />

      <div className="space-y-6">
        <h2 className="text-xl font-bold">Reviews</h2>
        <ReviewForm productId={productId} />
        <ReviewList productId={productId} />
      </div>

      <Separator />

      <SimilarProducts productId={productId} />
    </div>
  );
}
