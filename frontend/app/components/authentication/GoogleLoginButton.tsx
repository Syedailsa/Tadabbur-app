import React from "react";
import { GoogleLogin } from "@react-oauth/google";
import axios from "axios";
import {
  GoogleCredentialResponse,
  GoogleSignInRequest,
  GoogleSignInResponse,
  GoogleLoginProps,
} from "../../utils/types";

export default function GoogleLoginButton({
  onSuccess,
  onLoading,
  onError,
  text = "signin_with",
}: GoogleLoginProps) {
  const handleGoogleSuccess = async (credentialResponse: GoogleCredentialResponse): Promise<void> => {
    onLoading(true);
    try {
      if (!credentialResponse.credential) {
        throw new Error("No credential received");
      }
      const request: GoogleSignInRequest = { token: credentialResponse.credential };
      const res = await axios.post<GoogleSignInResponse>(`${process.env.NEXT_PUBLIC_BACKEND_URL}/auth/google-signin`, request);
      onSuccess(res.data);
    } catch (error) {
      onLoading(false);
      onError(`Google authentication failed. Please try again: ${error}`);
    }
  };

  return (
    <div className="flex justify-center w-full">
      <GoogleLogin
        onSuccess={handleGoogleSuccess}
        onError={() => {
          onError("Google Login Failed");
          onLoading(false);
        }}
        theme="filled_blue"
        shape="pill"
        text={text}
      />
    </div>
  );
}
