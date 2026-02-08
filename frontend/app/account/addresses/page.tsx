"use client";

import { useState } from "react";
import { useAddresses, useCreateAddress, useUpdateAddress, useDeleteAddress, useSetDefaultAddress } from "@/hooks/use-addresses";
import { AddressForm } from "@/components/account/address-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Pencil, Trash2, Star } from "lucide-react";
import type { Address } from "@/types";

export default function AddressesPage() {
  const { data: addresses, isLoading } = useAddresses();
  const createAddress = useCreateAddress();
  const updateAddress = useUpdateAddress();
  const deleteAddress = useDeleteAddress();
  const setDefault = useSetDefaultAddress();

  const [showForm, setShowForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState<Address | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }, (_, i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Addresses</h2>
        {!showForm && !editingAddress && (
          <Button size="sm" onClick={() => setShowForm(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Add Address
          </Button>
        )}
      </div>

      {(showForm || editingAddress) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{editingAddress ? "Edit" : "New"} Address</CardTitle>
          </CardHeader>
          <CardContent>
            <AddressForm
              address={editingAddress || undefined}
              isPending={createAddress.isPending || updateAddress.isPending}
              onSubmit={(data) => {
                if (editingAddress) {
                  updateAddress.mutate({ id: editingAddress.id, ...data }, {
                    onSuccess: () => setEditingAddress(null),
                  });
                } else {
                  createAddress.mutate(data, {
                    onSuccess: () => setShowForm(false),
                  });
                }
              }}
              onCancel={() => {
                setShowForm(false);
                setEditingAddress(null);
              }}
            />
          </CardContent>
        </Card>
      )}

      {(!addresses || addresses.length === 0) && !showForm && (
        <p className="text-muted-foreground text-center py-8">No addresses saved yet.</p>
      )}

      <div className="grid gap-4">
        {addresses?.map((addr) => (
          <Card key={addr.id}>
            <CardContent className="flex items-start justify-between p-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{addr.label || `${addr.type} address`}</span>
                  <Badge variant="outline" className="text-xs capitalize">{addr.type}</Badge>
                  {addr.is_default && (
                    <Badge variant="secondary" className="text-xs">Default</Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  {addr.first_name} {addr.last_name}
                </p>
                <p className="text-sm text-muted-foreground">
                  {addr.address_line_1}
                  {addr.address_line_2 && `, ${addr.address_line_2}`}
                </p>
                <p className="text-sm text-muted-foreground">
                  {addr.city}, {addr.state} {addr.postal_code}, {addr.country}
                </p>
                {addr.phone && (
                  <p className="text-sm text-muted-foreground">{addr.phone}</p>
                )}
              </div>
              <div className="flex gap-1">
                {!addr.is_default && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => setDefault.mutate(addr.id)}
                    title="Set as default"
                  >
                    <Star className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => {
                    setShowForm(false);
                    setEditingAddress(addr);
                  }}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive"
                  onClick={() => deleteAddress.mutate(addr.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
