"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

type Step = "EMAIL" | "OTP" | "PASSWORD" | "SUCCESS";

interface ForgotPasswordProps {
  onBackToLogin: () => void;
}

export default function ForgotPassword({ onBackToLogin }: ForgotPasswordProps) {
  const [step, setStep] = useState<Step>("EMAIL");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Form Data
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const API_URL = "http://localhost:8000/auth"; // Adjust if needed

  // 1. Send Email
  const handleSendEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to send OTP");
      setStep("OTP");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 2. Verify OTP
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Invalid OTP");
      setStep("PASSWORD");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. Change Password
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/change-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, new_password: newPassword }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to change password");
      setStep("SUCCESS");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-xl shadow-lg">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900">Reset Password</h2>
        <p className="text-sm text-gray-500 mt-2">
          {step === "EMAIL" && "Enter your email to receive a code"}
          {step === "OTP" && `Enter the code sent to ${email}`}
          {step === "PASSWORD" && "Create a new secure password"}
        </p>
      </div>

      <AnimatePresence mode="wait">
        {error && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
            className="p-3 text-sm text-red-600 bg-red-50 rounded-md"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {step === "EMAIL" && (
        <form onSubmit={handleSendEmail} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400"
          >
            {loading ? "Sending..." : "Send Reset Code"}
          </button>
        </form>
      )}

      {step === "OTP" && (
        <form onSubmit={handleVerifyOtp} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">OTP Code</label>
            <input
              type="text"
              required
              maxLength={4}
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm tracking-widest text-center text-xl font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400"
          >
            {loading ? "Verifying..." : "Verify Code"}
          </button>
          <button
            type="button"
            onClick={() => setStep("EMAIL")}
            className="w-full text-sm text-gray-600 hover:text-gray-900"
          >
            Use a different email
          </button>
        </form>
      )}

      {step === "PASSWORD" && (
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">New Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400"
          >
            {loading ? "Updating..." : "Update Password"}
          </button>
        </form>
      )}

      {step === "SUCCESS" && (
        <div className="text-center space-y-4">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
            <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900">Password Updated!</h3>
          <p className="text-sm text-gray-500">
            You can now log in with your new password.
          </p>
          <button
            onClick={onBackToLogin}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Back to Login
          </button>
        </div>
      )}

      {step !== "SUCCESS" && (
        <div className="mt-4 text-center">
          <button onClick={onBackToLogin} className="text-sm text-indigo-600 hover:text-indigo-500">
            Back to Sign In
          </button>
        </div>
      )}
    </div>
  );
}
