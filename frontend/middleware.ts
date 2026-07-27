// middleware.ts
//
// Next.js middleware runs before EVERY request.
// We use it to protect dashboard routes —
// redirect to login if no token found.
//
// NOTE: Middleware runs on the SERVER so we can't
// access localStorage. We use cookies instead.
// For now we check the token from the request headers.

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const PROTECTED_ROUTES = ['/dashboard']

// Routes that should redirect to dashboard if already logged in
const AUTH_ROUTES = ['/login', '/register']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Get token from cookie (we'll set this on login)
  const token = request.cookies.get('token')?.value

  // If trying to access protected route without token
  const isProtectedRoute = PROTECTED_ROUTES.some(route =>
    pathname.startsWith(route)
  )

  if (isProtectedRoute && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // If already logged in and trying to access auth pages
  const isAuthRoute = AUTH_ROUTES.some(route =>
    pathname.startsWith(route)
  )

  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

export const config = {
  // Only run middleware on these paths
  matcher: ['/dashboard/:path*', '/login', '/register']
}