"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { Input } from "@/components/ui/input";
import { formatPrice, proxyImageUrl } from "@/lib/utils";
import { Search, Loader2 } from "lucide-react";
import type { Product } from "@/types";

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);

  const { data: results, isLoading } = useQuery<Product[]>({
    queryKey: ["search", debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery.trim()) return [];
      const res = await api.get(`/products?search=${encodeURIComponent(debouncedQuery.trim())}&per_page=5`);
      return res.data.data || [];
    },
    enabled: debouncedQuery.trim().length > 0,
  });

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Open dropdown when we have results
  useEffect(() => {
    if (debouncedQuery.trim() && results && results.length > 0) {
      setIsOpen(true);
    }
  }, [debouncedQuery, results]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setIsOpen(false);
      router.push(`/products?search=${encodeURIComponent(query.trim())}`);
    }
  };

  const handleSelect = (productId: number) => {
    setIsOpen(false);
    setQuery("");
    router.push(`/products/${productId}`);
  };

  return (
    <div ref={containerRef} className="relative w-full">
      <form onSubmit={handleSubmit}>
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search products..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (debouncedQuery.trim() && results && results.length > 0) {
              setIsOpen(true);
            }
          }}
          className="pl-9"
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
        )}
      </form>

      {/* Dropdown Results */}
      {isOpen && debouncedQuery.trim() && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-background/95 backdrop-blur-xl border rounded-xl shadow-xl z-50 max-h-80 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              Searching...
            </div>
          ) : results && results.length > 0 ? (
            <>
              {results.map((product) => {
                const primaryImage = product.images?.find((img) => img.is_primary) || product.images?.[0];
                return (
                  <button
                    key={product.id}
                    onClick={() => handleSelect(product.id)}
                    className="w-full flex items-center gap-3 p-3 hover:bg-accent/50 text-left transition-all duration-200 rounded-lg mx-1 first:mt-1"
                  >
                    <div className="relative w-10 h-10 flex-shrink-0 rounded-lg bg-muted overflow-hidden">
                      {primaryImage ? (
                        <Image
                          src={proxyImageUrl(primaryImage.url)}
                          alt={product.name}
                          fill
                          className="object-cover"
                          sizes="40px"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                          -
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium line-clamp-1">{product.name}</p>
                      <p className="text-sm text-primary font-semibold">
                        ${formatPrice(product.price)}
                      </p>
                    </div>
                  </button>
                );
              })}
              <Link
                href={`/products?search=${encodeURIComponent(query.trim())}`}
                onClick={() => setIsOpen(false)}
                className="block p-3 text-center text-sm text-primary hover:bg-accent/50 transition-all duration-200 border-t"
              >
                View all results
              </Link>
            </>
          ) : (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No products found
            </div>
          )}
        </div>
      )}
    </div>
  );
}
