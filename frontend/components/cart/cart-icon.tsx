"use client";

import Link from "next/link";
import { useCartStore } from "@/stores/cart-store";
import { useHydration } from "@/hooks/use-hydration";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShoppingCart } from "lucide-react";

export function CartIcon() {
  const { itemCount } = useCartStore();
  const hydrated = useHydration();

  return (
    <Button variant="ghost" size="icon" asChild className="relative">
      <Link href="/cart">
        <ShoppingCart className="h-5 w-5" />
        {hydrated && itemCount > 0 && (
          <Badge
            variant="gradient"
            className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
          >
            {itemCount > 99 ? "99+" : itemCount}
          </Badge>
        )}
        <span className="sr-only">Cart</span>
      </Link>
    </Button>
  );
}
