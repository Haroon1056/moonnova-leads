import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

interface ProtectedRouteProps {
  adminOnly?: boolean;
}

export function ProtectedRoute({ adminOnly = false }: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, accessToken, user } = useAuthStore();

  if (!isAuthenticated || !accessToken) {
    return <Navigate to="/auth/login" replace state={{ from: location }} />;
  }

  if (adminOnly && !user?.is_staff && !user?.is_superuser) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}