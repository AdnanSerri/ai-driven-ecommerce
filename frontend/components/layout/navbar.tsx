"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import { useAuthStore } from "@/stores/auth-store";
import { useLogout } from "@/hooks/use-auth";
import { useHydration } from "@/hooks/use-hydration";
import { CartIcon } from "@/components/cart/cart-icon";
import { SearchBar } from "@/components/layout/search-bar";
import { MobileNav } from "@/components/layout/mobile-nav";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, LogOut, Package, Heart, MapPin, Star, Sun, Moon } from "lucide-react";

export function Navbar() {
  const { user, token } = useAuthStore();
  const logout = useLogout();
  const hydrated = useHydration();
  const { theme, setTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
      <div className="h-px w-full gradient-primary opacity-50" />
      <div className="container mx-auto flex h-16 items-center gap-4 px-4">
        <MobileNav />

        <Link href="/" className="mr-4 flex items-center gap-2 font-bold text-xl gradient-primary-text">
          ShopAI
        </Link>

        <nav className="hidden md:flex items-center gap-6 text-sm">
          <Link href="/products" className="nav-link-underline text-muted-foreground hover:text-foreground transition-colors">
            Products
          </Link>
          <Link href="/categories" className="nav-link-underline text-muted-foreground hover:text-foreground transition-colors">
            Categories
          </Link>
        </nav>

        <div className="flex-1 hidden md:block max-w-md mx-4">
          <SearchBar />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="rounded-full"
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>

          {!hydrated ? (
            <Skeleton className="h-8 w-20" />
          ) : token ? (
            <>
              <CartIcon />
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="rounded-full">
                    <Avatar className="h-8 w-8 transition-all hover:ring-2 hover:ring-primary/30">
                      <AvatarFallback>
                        {user?.name?.charAt(0).toUpperCase() || "U"}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <div className="px-2 py-1.5 text-sm font-medium">
                    {user?.name}
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/account" className="cursor-pointer">
                      <User className="mr-2 h-4 w-4" />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/account/orders" className="cursor-pointer">
                      <Package className="mr-2 h-4 w-4" />
                      Orders
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/account/wishlist" className="cursor-pointer">
                      <Heart className="mr-2 h-4 w-4" />
                      Wishlist
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/account/addresses" className="cursor-pointer">
                      <MapPin className="mr-2 h-4 w-4" />
                      Addresses
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/account/reviews" className="cursor-pointer">
                      <Star className="mr-2 h-4 w-4" />
                      My Reviews
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => logout.mutate()}
                    className="cursor-pointer text-destructive"
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" asChild>
                <Link href="/login">Login</Link>
              </Button>
              <Button variant="gradient" size="pill-sm" asChild>
                <Link href="/register">Register</Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
