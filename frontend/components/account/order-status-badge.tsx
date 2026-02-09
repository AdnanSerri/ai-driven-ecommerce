import { Badge } from "@/components/ui/badge";

const statusConfig: Record<string, { variant: "warning" | "info" | "default" | "success" | "destructive" | "secondary"; label: string }> = {
  pending: { variant: "warning", label: "Pending" },
  confirmed: { variant: "info", label: "Confirmed" },
  processing: { variant: "info", label: "Processing" },
  shipped: { variant: "default", label: "Shipped" },
  delivered: { variant: "success", label: "Delivered" },
  cancelled: { variant: "destructive", label: "Cancelled" },
};

interface OrderStatusBadgeProps {
  status: string;
}

export function OrderStatusBadge({ status }: OrderStatusBadgeProps) {
  const config = statusConfig[status] || { variant: "secondary" as const, label: status };
  return (
    <Badge variant={config.variant}>
      {config.label}
    </Badge>
  );
}
