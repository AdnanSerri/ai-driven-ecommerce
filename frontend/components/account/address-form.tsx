"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2 } from "lucide-react";
import type { Address } from "@/types";

interface AddressFormProps {
  address?: Address;
  onSubmit: (data: any) => void;
  isPending: boolean;
  onCancel: () => void;
}

export function AddressForm({ address, onSubmit, isPending, onCancel }: AddressFormProps) {
  const [form, setForm] = useState({
    label: "",
    type: "shipping" as "shipping" | "billing",
    first_name: "",
    last_name: "",
    address_line_1: "",
    address_line_2: "",
    city: "",
    state: "",
    postal_code: "",
    country: "",
    phone: "",
    is_default: false,
  });

  useEffect(() => {
    if (address) {
      setForm({
        label: address.label || "",
        type: address.type,
        first_name: address.first_name,
        last_name: address.last_name,
        address_line_1: address.address_line_1,
        address_line_2: address.address_line_2 || "",
        city: address.city,
        state: address.state,
        postal_code: address.postal_code,
        country: address.country,
        phone: address.phone || "",
        is_default: address.is_default,
      });
    }
  }, [address]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  const update = (field: string, value: any) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Label (optional)</Label>
          <Input value={form.label} onChange={(e) => update("label", e.target.value)} placeholder="Home, Office..." />
        </div>
        <div className="space-y-2">
          <Label>Type</Label>
          <Select value={form.type} onValueChange={(v) => update("type", v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="shipping">Shipping</SelectItem>
              <SelectItem value="billing">Billing</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>First Name</Label>
          <Input value={form.first_name} onChange={(e) => update("first_name", e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label>Last Name</Label>
          <Input value={form.last_name} onChange={(e) => update("last_name", e.target.value)} required />
        </div>
      </div>
      <div className="space-y-2">
        <Label>Address Line 1</Label>
        <Input value={form.address_line_1} onChange={(e) => update("address_line_1", e.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label>Address Line 2 (optional)</Label>
        <Input value={form.address_line_2} onChange={(e) => update("address_line_2", e.target.value)} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>City</Label>
          <Input value={form.city} onChange={(e) => update("city", e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label>State</Label>
          <Input value={form.state} onChange={(e) => update("state", e.target.value)} required />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Postal Code</Label>
          <Input value={form.postal_code} onChange={(e) => update("postal_code", e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label>Country</Label>
          <Input value={form.country} onChange={(e) => update("country", e.target.value)} required />
        </div>
      </div>
      <div className="space-y-2">
        <Label>Phone (optional)</Label>
        <Input type="tel" value={form.phone} onChange={(e) => update("phone", e.target.value)} />
      </div>
      <div className="flex items-center gap-2">
        <Checkbox
          id="is-default"
          checked={form.is_default}
          onCheckedChange={(v) => update("is_default", !!v)}
        />
        <Label htmlFor="is-default" className="cursor-pointer">Set as default</Label>
      </div>
      <div className="flex gap-3">
        <Button type="submit" disabled={isPending}>
          {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          {address ? "Update" : "Add"} Address
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
