import Link from "next/link";
import { Separator } from "@/components/ui/separator";

export function Footer() {
  return (
    <footer className="border-t bg-muted/30 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="font-bold text-lg mb-3 gradient-primary-text">ShopAI</h3>
            <p className="text-sm text-muted-foreground">
              AI-powered e-commerce with personalized recommendations.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-3 text-sm">Quick Links</h4>
            <nav className="flex flex-col gap-2 text-sm text-muted-foreground">
              <Link href="/products" className="hover:text-primary transition-colors">Products</Link>
              <Link href="/cart" className="hover:text-primary transition-colors">Cart</Link>
              <Link href="/account/orders" className="hover:text-primary transition-colors">Orders</Link>
            </nav>
          </div>
          <div>
            <h4 className="font-semibold mb-3 text-sm">Account</h4>
            <nav className="flex flex-col gap-2 text-sm text-muted-foreground">
              <Link href="/account" className="hover:text-primary transition-colors">Profile</Link>
              <Link href="/account/wishlist" className="hover:text-primary transition-colors">Wishlist</Link>
              <Link href="/account/addresses" className="hover:text-primary transition-colors">Addresses</Link>
            </nav>
          </div>
        </div>
        <Separator className="my-6" />
        <p className="text-center text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} ShopAI. Graduation Project.
        </p>
      </div>
    </footer>
  );
}
