import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';

interface GoogleLoginProps {
  onSuccess: (data: any) => void;
  onError: (message: string) => void;
  text?: "signin_with" | "signup_with";
}

export default function GoogleLoginButton({ onSuccess, onError, text = "signin_with" }: GoogleLoginProps) {
  
  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      // Matches your backend model: class GoogleSignInRequest(BaseModel): token: str
      const res = await axios.post('http://localhost:8000/auth/google-signin', {
        token: credentialResponse.credential
      });
      onSuccess(res.data);
    } catch (error) {
      onError("Google authentication failed. Please try again.");
    }
  };

  return (
    <div className="flex justify-center w-full">
      <GoogleLogin
        onSuccess={handleGoogleSuccess}
        onError={() => onError("Google Login Failed")}
        theme="filled_blue"
        shape="pill"
        text={text}
      />
    </div>
  );
}