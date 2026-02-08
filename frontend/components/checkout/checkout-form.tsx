"use client";

import { useState } from "react";
import Link from "next/link";
import { useCheckout } from "@/hooks/use-orders";
import { AddressSelector } from "@/components/checkout/address-selector";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export function CheckoutForm() {
  const [shippingAddressId, setShippingAddressId] = useState<number | undefined>();
  const [billingAddressId, setBillingAddressId] = useState<number | undefined>();
  const [notes, setNotes] = useState("");
  const checkout = useCheckout();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!shippingAddressId || !billingAddressId) return;
    checkout.mutate({
      shipping_address_id: shippingAddressId,
      billing_address_id: billingAddressId,
      notes: notes || undefined,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Shipping & Billing</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <AddressSelector
            label="Shipping Address"
            type="shipping"
            value={shippingAddressId}
            onChange={setShippingAddressId}
          />
          <AddressSelector
            label="Billing Address"
            type="billing"
            value={billingAddressId}
            onChange={setBillingAddressId}
          />

          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">Need to add or edit an address?</span>
            <Link
              href="/account/addresses"
              className="inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-md border border-primary text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
            >
              Manage Addresses
            </Link>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Order Notes (optional)</Label>
            <Textarea
              id="notes"
              placeholder="Special instructions for your order..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
          </div>

          <Button
            type="submit"
            size="lg"
            className="w-full"
            disabled={!shippingAddressId || !billingAddressId || checkout.isPending}
          >
            {checkout.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Place Order
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
