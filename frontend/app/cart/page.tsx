"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { AuthGuard } from "@/components/auth-guard";
import { useCart, useClearCart } from "@/hooks/use-cart";
import { CartItem } from "@/components/cart/cart-item";
import { CartSummary } from "@/components/cart/cart-summary";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ShoppingCart, Trash2 } from "lucide-react";
import { staggerContainer, staggerItem } from "@/lib/motion";

function CartContent() {
  const { data: cart, isLoading } = useCart();
  const clearCart = useClearCart();

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Skeleton className="h-8 w-32 mb-6" />
        <div className="grid md:grid-cols-3 gap-8">
          <div className="md:col-span-2 space-y-4">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <ShoppingCart className="h-16 w-16 mx-auto text-primary/40 mb-4" />
        <h1 className="text-2xl font-bold mb-2">Your cart is empty</h1>
        <p className="text-muted-foreground mb-6">Browse our products and add items to your cart.</p>
        <Button variant="gradient" size="pill" asChild>
          <Link href="/products">Continue Shopping</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Shopping Cart</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={() => clearCart.mutate()}
          disabled={clearCart.isPending}
          className="text-destructive"
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Clear Cart
        </Button>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        <motion.div
          className="md:col-span-2"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {cart.items.map((item) => (
            <motion.div key={item.id} variants={staggerItem}>
              <CartItem item={item} />
            </motion.div>
          ))}
        </motion.div>
        <div>
          <CartSummary cart={cart} />
        </div>
      </div>
    </div>
  );
}

export default function CartPage() {
  return (
    <AuthGuard>
      <CartContent />
    </AuthGuard>
  );
}
