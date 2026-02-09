import { Badge } from "@/components/ui/badge";

interface StockBadgeProps {
  quantity: number;
}

export function StockBadge({ quantity }: StockBadgeProps) {
  if (quantity <= 0) {
    return <Badge variant="destructive">Out of Stock</Badge>;
  }
  if (quantity <= 5) {
    return <Badge variant="warning">Only {quantity} left</Badge>;
  }
  return <Badge variant="success">In Stock</Badge>;
}
