"use client";

import { motion } from "framer-motion";
import { ProductCard } from "@/components/products/product-card";
import { Skeleton } from "@/components/ui/skeleton";
import { staggerContainer, staggerItem } from "@/lib/motion";
import type { Product } from "@/types";

interface ProductGridProps {
  products: Product[];
  isLoading?: boolean;
}

export function ProductGrid({ products, isLoading }: ProductGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {Array.from({ length: 8 }, (_, i) => (
          <div key={i} className="space-y-3">
            <Skeleton className="aspect-square w-full rounded-lg" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-6 w-1/3" />
          </div>
        ))}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">No products found</p>
        <p className="text-sm mt-1">Try adjusting your filters or search terms.</p>
      </div>
    );
  }

  return (
    <motion.div
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
    >
      {products.map((product) => (
        <motion.div key={product.id} variants={staggerItem}>
          <ProductCard product={product} />
        </motion.div>
      ))}
    </motion.div>
  );
}
