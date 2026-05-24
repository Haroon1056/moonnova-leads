import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

export function AdminOnlyRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((state) => state.user);
  const accessToken = useAuthStore((state) => state.accessToken);

  if (!accessToken) {
    return <Navigate to="/auth/login" replace />;
  }

  const isAdmin = Boolean(user?.is_staff || user?.is_superuser);

  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}