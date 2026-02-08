import { Badge } from "@/components/ui/badge";

const statusConfig: Record<string, { className: string; label: string }> = {
  pending: { className: "bg-yellow-100 text-yellow-700", label: "Pending" },
  confirmed: { className: "bg-blue-100 text-blue-700", label: "Confirmed" },
  processing: { className: "bg-indigo-100 text-indigo-700", label: "Processing" },
  shipped: { className: "bg-purple-100 text-purple-700", label: "Shipped" },
  delivered: { className: "bg-green-100 text-green-700", label: "Delivered" },
  cancelled: { className: "bg-red-100 text-red-700", label: "Cancelled" },
};

interface OrderStatusBadgeProps {
  status: string;
}

export function OrderStatusBadge({ status }: OrderStatusBadgeProps) {
  const config = statusConfig[status] || { className: "bg-gray-100 text-gray-700", label: status };
  return (
    <Badge variant="secondary" className={config.className}>
      {config.label}
    </Badge>
  );
}
