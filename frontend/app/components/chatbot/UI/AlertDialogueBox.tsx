"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, AlertCircle, Wifi, WifiOff } from "lucide-react";

interface AlertDialogueBoxProps {
  isOpen: boolean;
  onClose: () => void;
  type: "error" | "loading" | "success" | "warning";
  title: string;
  message: string;
  showRetryButton?: boolean;
  onRetry?: () => void;
  currentAttempt?: number;
  maxAttempts?: number;
  duration?: number;
}

const AlertDialogueBox = ({
  isOpen,
  onClose,
  type,
  title,
  message,
  showRetryButton = false,
  onRetry,
  currentAttempt,
  maxAttempts,
  duration,
}: AlertDialogueBoxProps) => {
  if (!isOpen) return null;

  const getIcon = () => {
    switch (type) {
      case "loading":
        return (
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
        );
      case "error":
        return <WifiOff className="w-12 h-12 text-red-500" />;
      case "success":
        return <Wifi className="w-12 h-12 text-green-500" />;
      case "warning":
        return <AlertCircle className="w-12 h-12 text-yellow-500" />;
    }
  };

  const getColors = () => {
    switch (type) {
      case "loading":
        return "border-blue-500 bg-blue-50";
      case "error":
        return "border-red-500 bg-red-50";
      case "success":
        return "border-green-500 bg-green-50";
      case "warning":
        return "border-yellow-500 bg-yellow-50";
    }
  };

  // Auto-close after duration (for non-loading alerts)
  useEffect(() => {
    if (duration && duration > 0 && type !== "loading") {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, type, onClose]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className={`relative w-full max-w-md mx-4 bg-white rounded-xl shadow-2xl border-2 ${getColors()} p-6`}
        >
          {/* Close button (only for non-loading states) */}
          {type !== "loading" && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}

          {/* Icon */}
          <div className="flex justify-center mb-4">{getIcon()}</div>

          {/* Title */}
          <h2 className="text-xl font-bold text-center text-gray-800 mb-2 switzer-600">
            {title}
          </h2>

          {/* Message */}
          <p className="text-center text-gray-600 mb-4 switzer-400">
            {message}
          </p>

          {/* Retry Progress */}
          {currentAttempt && maxAttempts && (
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Attempt {currentAttempt} of {maxAttempts}</span>
                <span>{Math.round((currentAttempt / maxAttempts) * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(currentAttempt / maxAttempts) * 100}%` }}
                  className="bg-blue-600 h-2 rounded-full transition-all"
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {type !== "loading" && (
            <div className="flex gap-3 mt-6">
              {showRetryButton && onRetry && (
                <button
                  onClick={onRetry}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors switzer-500"
                >
                  Retry Now
                </button>
              )}
              <button
                onClick={onClose}
                className={`${showRetryButton ? "flex-1" : "w-full"} bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-lg font-medium transition-colors switzer-500`}
              >
                {type === "error" ? "Close" : "OK"}
              </button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default AlertDialogueBox;
