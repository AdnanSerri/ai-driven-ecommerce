"use client";

import { use } from "react";
import Link from "next/link";
import { useOrder, useCancelOrder } from "@/hooks/use-orders";
import { formatPrice } from "@/lib/utils";
import { OrderStatusBadge } from "@/components/account/order-status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft } from "lucide-react";

export default function OrderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const orderId = Number(id);
  const { data: order, isLoading } = useOrder(orderId);
  const cancelOrder = useCancelOrder();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!order) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-bold">Order not found</h2>
      </div>
    );
  }

  const canCancel = ["pending", "confirmed"].includes(order.status);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/account/orders">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Link>
        </Button>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Order #{order.order_number}</h2>
          <p className="text-sm text-muted-foreground">
            Placed on {new Date(order.ordered_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <OrderStatusBadge status={order.status} />
          {canCancel && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => cancelOrder.mutate(orderId)}
              disabled={cancelOrder.isPending}
            >
              Cancel Order
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Items</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {order.items.map((item) => (
              <div key={item.id} className="flex justify-between text-sm py-2 border-b last:border-0">
                <div>
                  {item.product ? (
                    <Link
                      href={`/products/${item.product.id}`}
                      className="font-medium hover:text-primary"
                    >
                      {item.product_name}
                    </Link>
                  ) : (
                    <span className="font-medium">{item.product_name}</span>
                  )}
                  <p className="text-muted-foreground">
                    ${formatPrice(item.product_price)} x {item.quantity}
                  </p>
                </div>
                <p className="font-medium">${formatPrice(item.subtotal)}</p>
              </div>
            ))}
          </div>
          <Separator className="my-4" />
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Subtotal</span>
              <span>${formatPrice(order.subtotal)}</span>
            </div>
            {order.discount > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Discount</span>
                <span>-${formatPrice(order.discount)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tax</span>
              <span>${formatPrice(order.tax)}</span>
            </div>
            <Separator />
            <div className="flex justify-between font-bold text-base">
              <span>Total</span>
              <span>${formatPrice(order.total)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-4">
        {order.shipping_address && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Shipping Address</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              <p>{order.shipping_address.first_name} {order.shipping_address.last_name}</p>
              <p>{order.shipping_address.address_line_1}</p>
              {order.shipping_address.address_line_2 && <p>{order.shipping_address.address_line_2}</p>}
              <p>{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}</p>
              <p>{order.shipping_address.country}</p>
            </CardContent>
          </Card>
        )}
        {order.billing_address && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Billing Address</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              <p>{order.billing_address.first_name} {order.billing_address.last_name}</p>
              <p>{order.billing_address.address_line_1}</p>
              {order.billing_address.address_line_2 && <p>{order.billing_address.address_line_2}</p>}
              <p>{order.billing_address.city}, {order.billing_address.state} {order.billing_address.postal_code}</p>
              <p>{order.billing_address.country}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {order.notes && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Notes</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {order.notes}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
