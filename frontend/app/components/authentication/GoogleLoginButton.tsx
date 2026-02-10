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
  onError,
  text = "signin_with",
}: GoogleLoginProps) {
  const handleGoogleSuccess = async (credentialResponse: GoogleCredentialResponse): Promise<void> => {
    try {
      if (!credentialResponse.credential) {
        throw new Error("No credential received");
      }
      const request: GoogleSignInRequest = { token: credentialResponse.credential };
      const res = await axios.post<GoogleSignInResponse>(`${process.env.NEXT_BACKEND_URL}/auth/google-signin`, request);
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
