import React, { useState } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import axios, { AxiosError } from "axios";

const RegistrationSchema = z.object({
  username: z
    .string()
    .min(3, "Username must be at least 3 characters long")
    .max(20, "Username must be less than 20 characters"),
  age: z.coerce
    .number()
    .min(1, "Please enter a valid age")
    .max(120, "Please enter a valid age"),
});

export type RegistrationData = z.infer<typeof RegistrationSchema>;

interface RegistrationFormProps {
  onComplete: (data: RegistrationData) => void;
}

const RegistrationForm: React.FC<RegistrationFormProps> = ({ onComplete }) => {
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegistrationData>({

    // @ts-expect-error: ZodResolver type inference doesn't match useForm generic
    resolver: zodResolver(RegistrationSchema),
    defaultValues: {
      username: "user",
      age: 18,
    },
  });

  const onSubmit: SubmitHandler<RegistrationData> = async (data) => {
    setServerError(null);

    try {
      const token = localStorage.getItem("token");

      if (!token) {
        throw new Error("User not authenticated");
      }

      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/personalization/save`,
        {
          username: data.username,
          age: data.age,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data.is_personalized) {
        localStorage.setItem("personalization", JSON.stringify(data));
        onComplete(data);
      }
    } catch (error) {
      const err = error as AxiosError<{ detail?: string }>
      console.error("Personalization error:", err);
      setServerError(
        err.response?.data?.detail ||
        "Failed to save personalization. Please try again."
      );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md bg-white rounded-xl shadow-xl border border-black/5 overflow-hidden"
      >
        <div className="bg-gray-50 px-8 py-6 border-b border-gray-100">
          <h2 className="text-2xl font-bold text-gray-800 switzer-600">
            Welcome to Tadabbur
          </h2>
          <p className="text-gray-500 text-sm mt-1 switzer-400">
            Tell us a bit about yourself to personalize your experience.
          </p>
        </div>

        <form
          //@ts-expect-error any issues can't be resolved
          onSubmit={handleSubmit(onSubmit)}
          className="px-8 py-8 flex flex-col gap-y-5"
        >
          {serverError && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded">
              {serverError}
            </div>
          )}

          <div className="flex flex-col gap-y-1.5">
            <label
              htmlFor="username"
              className="text-sm font-medium text-gray-700 switzer-500"
            >
              What should we call you?
            </label>
            <input
              id="username"
              type="text"
              placeholder="e.g. Ali"
              className={`w-full px-4 py-2.5 rounded-lg border ${errors.username
                ? "border-red-500 focus:ring-red-200"
                : "border-gray-200 focus:ring-blue-100 focus:border-blue-500"
                } focus:outline-none focus:ring-4 transition-all duration-200 switzer-400`}
              {...register("username")}
            />
            {errors.username && (
              <p className="text-xs text-red-500 switzer-500">
                {errors.username.message}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-y-1.5">
            <label
              htmlFor="age"
              className="text-sm font-medium text-gray-700 switzer-500"
            >
              How old are you?
            </label>
            <input
              id="age"
              type="number"
              placeholder="e.g. 15"
              className={`w-full px-4 py-2.5 rounded-lg border ${errors.age
                ? "border-red-500 focus:ring-red-200"
                : "border-gray-200 focus:ring-blue-100 focus:border-blue-500"
                } focus:outline-none focus:ring-4 transition-all duration-200 switzer-400`}
              {...register("age")}
            />
            {errors.age && (
              <p className="text-xs text-red-500 switzer-500">
                {errors.age.message}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 w-full bg-black text-white font-medium py-3 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50 switzer-500 shadow-md cursor-pointer"
          >
            {isSubmitting ? "Saving..." : "Start Chatting"}
          </button>
        </form>
      </motion.div>
    </div>
  );
};

export default RegistrationForm;