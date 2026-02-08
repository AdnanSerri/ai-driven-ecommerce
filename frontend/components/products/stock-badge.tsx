import { Badge } from "@/components/ui/badge";

interface StockBadgeProps {
  quantity: number;
}

export function StockBadge({ quantity }: StockBadgeProps) {
  if (quantity <= 0) {
    return <Badge variant="destructive">Out of Stock</Badge>;
  }
  if (quantity <= 5) {
    return <Badge variant="secondary" className="bg-orange-100 text-orange-700">Only {quantity} left</Badge>;
  }
  return <Badge variant="secondary" className="bg-green-100 text-green-700">In Stock</Badge>;
}
