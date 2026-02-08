import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedPaths = ["/account", "/cart", "/checkout"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = protectedPaths.some((p) => pathname.startsWith(p));

  if (!isProtected) return NextResponse.next();

  const authCookie = request.cookies.get("auth-token");
  if (!authCookie?.value) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/account/:path*", "/cart/:path*", "/checkout/:path*"],
};
