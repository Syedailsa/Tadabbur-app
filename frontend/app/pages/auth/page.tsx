"use client";

import React, { useState, useEffect } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import LoginForm from '../../components/authentication/LoginForm';
import SignupForm from '../../components/authentication/SignupForm';
import GoogleLoginButton from '../../components/authentication/GoogleLoginButton';
import ForgotPassword from '../../components/authentication/ForgotPassword';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

type AuthView = 'LOGIN' | 'SIGNUP' | 'FORGOT';

export default function AuthPage() {
  const [view, setView] = useState<AuthView>('LOGIN');
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const router = useRouter();

  type AuthSuccessData = {
    token: string;
    user_id: string;
    firstname: string;
  };

  useEffect(() => {
    const token = Cookies.get('auth_token');
    if (token) {
      router.replace('/pages/chatbot');
    } else {
      setIsInitialLoading(false); // Only show the form if we AREN'T redirecting
    }
  }, [router]);

  if (isInitialLoading) {
    return (
       <div className="flex min-h-screen items-center justify-center bg-gray-100">
         <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
       </div>
    );
  }

  // const handleAuthSuccess = (data: AuthSuccessData) => {
  //   console.log("Auth Successful:", data);

  //   localStorage.setItem('token', data.token);
  //   localStorage.setItem('user', JSON.stringify({ 
  //     id: data.user_id,
  //     name: data.firstname
  //   }));

  //   router.push('/pages/chatbot');
  // };

  const handleAuthSuccess = (data: AuthSuccessData) => {
    setIsSubmitting(true);
    
    Cookies.set('auth_token', data.token, { expires: 7, path: '/' });

    localStorage.setItem('auth_token', data.token); 
    localStorage.setItem('user', JSON.stringify({
      id: data.user_id,
      name: data.firstname
    }));

    setTimeout(() => {
      router.push('/pages/chatbot');
    }, 100);
  };

  const getHeaderText = () => {
    if (view === 'FORGOT') return { title: 'Reset Password', sub: 'Recover your account access' };
    if (view === 'SIGNUP') return { title: 'Create Account', sub: 'Start your journey with us' };
    return { title: 'Welcome Back', sub: 'Enter your details to sign in' };
  };

  const { title, sub } = getHeaderText();

  return (
    <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!}>
      <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">

        {isSubmitting && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/60 backdrop-blur-sm pointer-events-auto">
            <div className="flex flex-col items-center">
              <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
              <p className="mt-4 font-medium text-blue-600">Authenticating</p>
            </div>
          </div>
        )}

        <div className="w-full max-w-md bg-white rounded-xl shadow-lg overflow-hidden">

          <div className="px-8 pt-8 pb-6 text-center">
            <h1 className="text-2xl font-bold text-gray-800">
              {title}
            </h1>
            <p className="text-sm text-gray-500 mt-2">
              {sub}
            </p>
          </div>

          {view !== 'FORGOT' && (
            <div className="px-8 mb-6">
              <div className="flex bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => { setView('LOGIN'); setGlobalError(null); }}
                  className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${view === 'LOGIN' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
                >
                  Sign In
                </button>
                <button
                  onClick={() => { setView('SIGNUP'); setGlobalError(null); }}
                  className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${view === 'SIGNUP' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
                >
                  Sign Up
                </button>
              </div>
            </div>
          )}

          <div className="px-8 pb-8">
            {globalError && (
              <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded border border-red-200">
                {globalError}
              </div>
            )}

            {view === 'LOGIN' && (
              <>
                <LoginForm onSuccess={handleAuthSuccess} onLoading={setIsSubmitting}/>
                <div className="mt-2 text-right">
                  <button
                    onClick={() => { setView('FORGOT'); setGlobalError(null); }}
                    className="text-sm text-indigo-600 hover:text-indigo-500"
                  >
                    Forgot password?
                  </button>
                </div>
              </>
            )}

            {view === 'SIGNUP' && (
              <SignupForm onSuccess={handleAuthSuccess} onLoading={setIsSubmitting}/>
            )}

            {view === 'FORGOT' && (
              <ForgotPassword onBackToLogin={() => { setView('LOGIN'); setGlobalError(null); }} onLoading={setIsSubmitting} />
            )}

            {view !== 'FORGOT' && (
              <>
                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">Or continue with</span>
                  </div>
                </div>

                <GoogleLoginButton
                  onSuccess={handleAuthSuccess}
                  onLoading={setIsSubmitting}
                  onError={setGlobalError}
                  text={view === 'LOGIN' ? "signin_with" : "signup_with"}
                />
              </>
            )}
          </div>

        </div>
      </div>
    </GoogleOAuthProvider>
  );
}