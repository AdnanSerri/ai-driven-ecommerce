import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPrice(value: string | number): string {
  return Number(value).toFixed(2)
}

export function proxyImageUrl(url: string): string {
  if (!url) return url;
  // Only proxy external URLs (Amazon CDN etc.), not local ones
  if (url.startsWith("/") || url.includes("localhost")) return url;
  return `/api/image-proxy?url=${encodeURIComponent(url)}`;
}
