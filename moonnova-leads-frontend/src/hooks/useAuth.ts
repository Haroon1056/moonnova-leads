import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/authStore";
import type { LoginPayload, RegisterPayload } from "@/types/auth";

function getApiError(error: any, fallback: string) {
  const data = error?.response?.data;
  return (
    data?.non_field_errors?.[0] ||
    data?.email?.[0] ||
    data?.password?.[0] ||
    data?.detail ||
    data?.error ||
    data?.message ||
    fallback
  );
}

export function useAuth() {
  const { user, accessToken, refreshToken, isAuthenticated, setAuth, setUser, logout } = useAuthStore();

  const profileQuery = useQuery({
    queryKey: ["auth", "profile"],
    queryFn: authService.profile,
    enabled: Boolean(accessToken),
    retry: false
  });

  const loginMutation = useMutation({
    mutationFn: (payload: LoginPayload) => authService.login(payload),
    onSuccess: (data) => {
      setAuth({
        user: data.user || null,
        accessToken: data.tokens.access,
        refreshToken: data.tokens.refresh
      });
      toast.success("Login successful");
    },
    onError: (error: any) => {
      toast.error(getApiError(error, "Login failed. Please check your email and password."));
    }
  });

  const registerMutation = useMutation({
    mutationFn: (payload: RegisterPayload) => authService.register(payload),
    onSuccess: (data) => {
      toast.success(data?.message || "Account created. Please verify your email.");
    },
    onError: (error: any) => {
      toast.error(getApiError(error, "Registration failed. Please check your details."));
    }
  });

  const verifyEmailMutation = useMutation({
    mutationFn: (token: string) => authService.verifyEmail(token),
    onSuccess: (data) => {
      setAuth({
        user: data.user || null,
        accessToken: data.tokens.access,
        refreshToken: data.tokens.refresh
      });
      toast.success(data?.message || "Email verified successfully");
    },
    onError: (error: any) => {
      toast.error(getApiError(error, "Verification failed. Please request a new link."));
    }
  });

  const resendVerificationMutation = useMutation({
    mutationFn: (email: string) => authService.resendVerification(email),
    onSuccess: (data: any) => toast.success(data?.message || "Verification email sent"),
    onError: (error: any) => toast.error(getApiError(error, "Failed to resend verification email."))
  });

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    setUser,
    logout,
    profileQuery,
    loginMutation,
    registerMutation,
    verifyEmailMutation,
    resendVerificationMutation
  };
}
