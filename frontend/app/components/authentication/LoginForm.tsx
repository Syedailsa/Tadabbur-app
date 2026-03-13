import React, {useEffect} from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import axios, { AxiosError } from 'axios';
import { loginSchema, LoginInputs, LoginProps, LoginResponse } from '@/app/utils/types';

export default function LoginForm({ onSuccess, onLoading }: LoginProps) {
  const [serverError, setServerError] = React.useState<string | null>(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginInputs>({
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    onLoading(isSubmitting);
  }, [isSubmitting, onLoading]);

  const onSubmit = async (data: LoginInputs) => {
    setServerError(null);
    try {
      const res = await axios.post<LoginResponse>(`${process.env.NEXT_PUBLIC_BACKEND_URL}/auth/login`, data);
      onSuccess(res.data);
    } catch (error) {
      const err = error as AxiosError<{ detail?: string }>
      setServerError(err.response?.data?.detail || "Invalid email or password");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {serverError && (
        <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded">
          {serverError}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          type="email"
          {...register("email")}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="john@example.com"
        />
        {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
        <input
          type="password"
          {...register("password")}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="••••••"
        />
        {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {isSubmitting ? 'Signing in...' : 'Sign In'}
      </button>
    </form>
  );
}