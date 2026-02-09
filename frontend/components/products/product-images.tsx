"use client";

import { useState } from "react";
import Image from "next/image";
import { cn, proxyImageUrl } from "@/lib/utils";
import type { ProductImage } from "@/types";

interface ProductImagesProps {
  images: ProductImage[];
  productName: string;
}

export function ProductImages({ images, productName }: ProductImagesProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (!images || images.length === 0) {
    return (
      <div className="aspect-square bg-muted rounded-xl flex items-center justify-center text-muted-foreground">
        No Image Available
      </div>
    );
  }

  const sorted = [...images].sort((a, b) => a.sort_order - b.sort_order);
  const selected = sorted[selectedIndex];

  return (
    <div className="space-y-3">
      <div className="relative aspect-square overflow-hidden rounded-xl bg-muted shadow-sm">
        <Image
          src={proxyImageUrl(selected.url)}
          alt={selected.alt_text || productName}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 50vw"
          priority
        />
      </div>
      {sorted.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {sorted.map((img, i) => (
            <button
              key={img.id}
              onClick={() => setSelectedIndex(i)}
              className={cn(
                "relative w-16 h-16 flex-shrink-0 rounded-md overflow-hidden border-2 transition-colors",
                i === selectedIndex ? "border-primary" : "border-transparent hover:border-muted-foreground/50"
              )}
            >
              <Image
                src={proxyImageUrl(img.url)}
                alt={img.alt_text || `${productName} ${i + 1}`}
                fill
                className="object-cover"
                sizes="64px"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
