"use client";

import Link from "next/link";
import { useState } from "react";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { SearchBar } from "@/components/layout/search-bar";
import { Menu, ShoppingBag, Grid3X3, Home } from "lucide-react";

export function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72">
        <div className="h-1 w-full gradient-primary rounded-full mb-4" />
        <SheetTitle className="font-bold text-xl mb-6 gradient-primary-text">ShopAI</SheetTitle>
        <div className="mb-4">
          <SearchBar />
        </div>
        <nav className="flex flex-col gap-3">
          <Link
            href="/"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 text-sm hover:text-primary text-muted-foreground transition-colors"
          >
            <Home className="h-4 w-4" />
            Home
          </Link>
          <Link
            href="/products"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 text-sm hover:text-primary text-muted-foreground transition-colors"
          >
            <ShoppingBag className="h-4 w-4" />
            Products
          </Link>
          <Link
            href="/categories"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 text-sm hover:text-primary text-muted-foreground transition-colors"
          >
            <Grid3X3 className="h-4 w-4" />
            Categories
          </Link>
        </nav>
      </SheetContent>
    </Sheet>
  );
}
