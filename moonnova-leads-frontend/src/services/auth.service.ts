import { api } from "@/lib/api";
import type {
  LoginPayload,
  LoginResponse,
  RegisterPayload,
  RegisterResponse,
  User
} from "@/types/auth";

export const authService = {
  async login(payload: LoginPayload) {
    const response = await api.post<LoginResponse>("/auth/login/", payload);
    return response.data;
  },

  async register(payload: RegisterPayload) {
    const response = await api.post<RegisterResponse>(
      "/auth/register/",
      payload
    );
    return response.data;
  },

  async profile() {
    const response = await api.get<User>("/auth/profile/");
    return response.data;
  },

  async logout() {
    const response = await api.post("/auth/logout/");
    return response.data;
  },

  async resendVerification(email: string) {
    const response = await api.post("/auth/resend-verification/", { email });
    return response.data;
  },

  async verifyEmail(token: string) {
    const response = await api.get<LoginResponse>(`/auth/verify-email/${token}/`);
    return response.data;
  }
};