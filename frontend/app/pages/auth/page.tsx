"use client";

import React, { useState } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import LoginForm from '../../components/authentication/LoginForm';
import SignupForm from '../../components/authentication/SignupForm';
import GoogleLoginButton from '../../components/authentication/GoogleLoginButton';
import ForgotPassword from '../../components/authentication/ForgotPassword';

export default function AuthPage() {
  const [isLoginView, setIsLoginView] = useState(true);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const handleAuthSuccess = (data: any) => {
    console.log("Auth Successful:", data);
    
    sessionStorage.setItem('token', data.token);
    sessionStorage.setItem('user', JSON.stringify({ 
      id: data.user_id, 
      name: data.firstname 
    })); 

    window.location.href = '/pages/chatbot';
  };

  return (
    <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!}>
      <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
        <div className="w-full max-w-md bg-white rounded-xl shadow-lg overflow-hidden">
          
          <div className="px-8 pt-8 pb-6 text-center">
            <h1 className="text-2xl font-bold text-gray-800">
              {isLoginView ? 'Welcome Back' : 'Create Account'}
            </h1>
            <p className="text-sm text-gray-500 mt-2">
              {isLoginView ? 'Enter your details to sign in' : 'Start your journey with us'}
            </p>
          </div>

          <div className="px-8 mb-6">
            <div className="flex bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => { setIsLoginView(true); setGlobalError(null); }}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                  isLoginView ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Sign In
              </button>
              <button
                onClick={() => { setIsLoginView(false); setGlobalError(null); }}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                  !isLoginView ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Sign Up
              </button>
            </div>
          </div>

          {/* Form Container */}
          <div className="px-8 pb-8">
            {globalError && (
              <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded border border-red-200">
                {globalError}
              </div>
            )}

            {/* Render the appropriate form */}
            {isLoginView ? (
              <LoginForm onSuccess={handleAuthSuccess} />
            ) : (
              <SignupForm onSuccess={handleAuthSuccess} />
            )}

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or continue with</span>
              </div>
            </div>

            {/* Google Button */}
            <GoogleLoginButton 
              onSuccess={handleAuthSuccess}
              onError={setGlobalError}
              text={isLoginView ? "signin_with" : "signup_with"}
            />
          </div>

        </div>
      </div>
    </GoogleOAuthProvider>
  );
}