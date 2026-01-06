"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function MainPage() {
  const router = useRouter();

  useEffect(() => {
    router.push('/pages/auth');
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <p>Loading...</p>
    </div>
  );
}