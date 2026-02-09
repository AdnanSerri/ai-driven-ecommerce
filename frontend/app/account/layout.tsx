"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { cn } from "@/lib/utils";
import { User, Package, MapPin, Heart, Star } from "lucide-react";

const sidebarItems = [
  { href: "/account", label: "Profile", icon: User },
  { href: "/account/orders", label: "Orders", icon: Package },
  { href: "/account/addresses", label: "Addresses", icon: MapPin },
  { href: "/account/wishlist", label: "Wishlist", icon: Heart },
  { href: "/account/reviews", label: "My Reviews", icon: Star },
];

function AccountLayoutInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">My Account</h1>
      <div className="flex flex-col md:flex-row gap-8">
        <aside className="md:w-56 flex-shrink-0">
          <nav className="flex md:flex-col gap-1 overflow-x-auto">
            {sidebarItems.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-full text-sm whitespace-nowrap transition-all",
                  pathname === href
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent text-muted-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
          </nav>
        </aside>
        <div className="flex-1 min-w-0">{children}</div>
      </div>
    </div>
  );
}

export default function AccountLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <AccountLayoutInner>{children}</AccountLayoutInner>
    </AuthGuard>
  );
}
