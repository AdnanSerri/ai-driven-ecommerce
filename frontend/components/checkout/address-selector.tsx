"use client";

import { useEffect } from "react";
import { useAddresses } from "@/hooks/use-addresses";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Address } from "@/types";

interface AddressSelectorProps {
  label: string;
  type: "shipping" | "billing";
  value?: number;
  onChange: (id: number) => void;
}

export function AddressSelector({ label, type, value, onChange }: AddressSelectorProps) {
  const { data: addresses, isLoading } = useAddresses();

  const filtered = addresses?.filter((a) => a.type === type) ?? [];

  // Auto-select default address when addresses load
  useEffect(() => {
    if (!value && filtered.length > 0) {
      const defaultAddr = filtered.find((a) => a.is_default);
      if (defaultAddr) {
        onChange(defaultAddr.id);
      } else if (filtered.length === 1) {
        // If only one address, select it automatically
        onChange(filtered[0].id);
      }
    }
  }, [filtered, value, onChange]);

  const formatAddress = (a: Address) =>
    `${a.first_name} ${a.last_name}, ${a.address_line_1}, ${a.city}, ${a.state} ${a.postal_code}`;

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Select
        value={value ? String(value) : undefined}
        onValueChange={(v) => onChange(Number(v))}
        disabled={isLoading}
      >
        <SelectTrigger>
          <SelectValue placeholder={`Select ${type} address`} />
        </SelectTrigger>
        <SelectContent>
          {filtered.length === 0 && (
            <SelectItem value="none" disabled>
              No {type} addresses found
            </SelectItem>
          )}
          {filtered.map((addr) => (
            <SelectItem key={addr.id} value={String(addr.id)}>
              {addr.label || formatAddress(addr)}
              {addr.is_default && " (Default)"}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
