import Image from "next/image";
import { formatPrice, proxyImageUrl } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Cart } from "@/types";

interface OrderSummaryProps {
  cart: Cart;
}

export function OrderSummary({ cart }: OrderSummaryProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Order Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {cart.items.map((item) => {
          const img = item.product?.images?.find((i) => i.is_primary) || item.product?.images?.[0];
          return (
            <div key={item.id} className="flex gap-3 text-sm">
              <div className="relative w-12 h-12 flex-shrink-0 rounded bg-muted overflow-hidden">
                {img ? (
                  <Image src={proxyImageUrl(img.url)} alt={item.product?.name || ""} fill className="object-cover" sizes="48px" />
                ) : (
                  <div className="flex h-full items-center justify-center text-xs text-muted-foreground">-</div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium line-clamp-1">{item.product?.name}</p>
                <p className="text-muted-foreground">Qty: {item.quantity}</p>
              </div>
              <p className="font-medium">${formatPrice(Number(item.price) * item.quantity)}</p>
            </div>
          );
        })}
        <Separator />
        <div className="flex justify-between font-bold">
          <span>Total</span>
          <span>${formatPrice(cart.total)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
