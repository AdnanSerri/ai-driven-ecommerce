"use client";

import Link from "next/link";
import { AuthGuard } from "@/components/auth-guard";
import { useCart } from "@/hooks/use-cart";
import { CheckoutForm } from "@/components/checkout/checkout-form";
import { OrderSummary } from "@/components/checkout/order-summary";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ShoppingCart } from "lucide-react";

function CheckoutContent() {
  const { data: cart, isLoading } = useCart();

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Skeleton className="h-8 w-32 mb-6" />
        <div className="grid md:grid-cols-2 gap-8">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <ShoppingCart className="h-16 w-16 mx-auto text-primary/40 mb-4" />
        <h1 className="text-2xl font-bold mb-2">Cart is empty</h1>
        <p className="text-muted-foreground mb-6">Add items to your cart before checking out.</p>
        <Button variant="gradient" size="pill" asChild>
          <Link href="/products">Browse Products</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Checkout</h1>
      <div className="grid md:grid-cols-2 gap-8">
        <CheckoutForm />
        <OrderSummary cart={cart} />
      </div>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <AuthGuard>
      <CheckoutContent />
    </AuthGuard>
  );
}
