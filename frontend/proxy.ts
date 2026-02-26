import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  const token = request.cookies.get('auth_token')?.value;
  const { pathname } = request.nextUrl;

  // 1. If user has a token and is on the auth page, proxy them to the chatbot
  if (token && pathname.startsWith('/pages/auth')) {
    return NextResponse.redirect(new URL('/pages/chatbot', request.url));
  }

  // 2. If user has NO token and tries to access the chatbot, proxy them to login
  if (!token && pathname.startsWith('/pages/chatbot')) {
    return NextResponse.redirect(new URL('/pages/auth', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/pages/auth', 
    '/pages/chatbot/:path*',
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}