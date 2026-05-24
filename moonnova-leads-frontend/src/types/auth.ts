export interface User {
  id: number;
  email: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  is_staff?: boolean;
  is_superuser?: boolean;
  is_active?: boolean;
  is_verified?: boolean;
  date_joined?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  full_name: string;
  email: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  message?: string;
  user: User;
  tokens: AuthTokens;
}

export interface RegisterResponse {
  message?: string;
  user?: User;
  verification_required?: boolean;
}

export interface AuthUser {
  id: number;
  email: string;
  full_name?: string;
  is_verified?: boolean;
  auth_provider?: string;
  profile_picture?: string | null;
  date_joined?: string;

  is_staff?: boolean;
  is_superuser?: boolean;
}