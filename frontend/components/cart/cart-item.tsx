"use client";

import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useUpdateCartItem, useRemoveCartItem } from "@/hooks/use-cart";
import { formatPrice, proxyImageUrl } from "@/lib/utils";
import { Minus, Plus, Trash2 } from "lucide-react";
import type { CartItem as CartItemType } from "@/types";

interface CartItemProps {
  item: CartItemType;
}

export function CartItem({ item }: CartItemProps) {
  const updateItem = useUpdateCartItem();
  const removeItem = useRemoveCartItem();

  const primaryImage = item.product?.images?.find((img) => img.is_primary) || item.product?.images?.[0];

  return (
    <div className="flex gap-4 py-4 border-b last:border-0 hover:bg-accent/30 rounded-lg transition-colors px-2 -mx-2">
      <div className="relative w-20 h-20 flex-shrink-0 rounded-md overflow-hidden bg-muted">
        {primaryImage ? (
          <Image
            src={proxyImageUrl(primaryImage.url)}
            alt={item.product?.name || "Product"}
            fill
            className="object-cover"
            sizes="80px"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
            No Image
          </div>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <Link
          href={`/products/${item.product_id}`}
          className="font-medium text-sm hover:text-primary line-clamp-2"
        >
          {item.product?.name || `Product #${item.product_id}`}
        </Link>
        <p className="text-sm font-bold mt-1">${formatPrice(item.price)}</p>

        <div className="flex items-center gap-2 mt-2">
          <div className="flex items-center border rounded-md">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-r-none"
              onClick={() =>
                updateItem.mutate({ id: item.id, quantity: Math.max(1, item.quantity - 1) })
              }
              disabled={item.quantity <= 1 || updateItem.isPending}
            >
              <Minus className="h-3 w-3" />
            </Button>
            <span className="w-8 text-center text-sm">{item.quantity}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-l-none"
              onClick={() => updateItem.mutate({ id: item.id, quantity: item.quantity + 1 })}
              disabled={updateItem.isPending}
            >
              <Plus className="h-3 w-3" />
            </Button>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-destructive hover:text-destructive"
            onClick={() => removeItem.mutate(item.id)}
            disabled={removeItem.isPending}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="text-right">
        <p className="font-bold">${formatPrice(Number(item.price) * item.quantity)}</p>
      </div>
    </div>
  );
}
