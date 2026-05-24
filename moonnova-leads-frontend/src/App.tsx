import { Navigate, Route, Routes } from "react-router-dom";

import { AuthLayout } from "@/components/layout/AuthLayout";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { AdminOnlyRoute } from "@/components/auth/AdminOnlyRoute";

import { LandingPage } from "@/pages/LandingPage";

import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";
import { ForgotPasswordPage } from "@/pages/auth/ForgotPasswordPage";
import { VerifyEmailPage } from "@/pages/auth/VerifyEmailPage";

import { DashboardHomePage } from "@/pages/dashboard/DashboardHomePage";
import { SearchesPage } from "@/pages/dashboard/SearchesPage";
import { SearchDetailPage } from "@/pages/dashboard/SearchDetailPage";
import { LeadsPage } from "@/pages/dashboard/LeadsPage";
import { AIPage } from "@/pages/dashboard/AIPage";
import { ExportsPage } from "@/pages/dashboard/ExportsPage";
import { UsagePage } from "@/pages/dashboard/UsagePage";
import { SettingsPage } from "@/pages/dashboard/SettingsPage";
import { AdminPage } from "@/pages/dashboard/AdminPage";

export default function App() {
  return (
    <Routes>
      {/* Public landing page */}
      <Route path="/" element={<LandingPage />} />

      {/* Public email verification route from backend email link */}
      <Route path="/verify-email/:token" element={<VerifyEmailPage />} />

      {/* Auth pages */}
      <Route path="/auth" element={<AuthLayout />}>
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="forgot-password" element={<ForgotPasswordPage />} />
        <Route path="verify-email" element={<VerifyEmailPage />} />
        <Route path="verify-email/:token" element={<VerifyEmailPage />} />
      </Route>

      {/* Protected dashboard */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<DashboardHomePage />} />
          <Route path="searches" element={<SearchesPage />} />
          <Route path="searches/:id" element={<SearchDetailPage />} />
          <Route path="leads" element={<LeadsPage />} />
          <Route path="ai" element={<AIPage />} />
          <Route path="exports" element={<ExportsPage />} />
          <Route path="usage" element={<UsagePage />} />
          <Route path="settings" element={<SettingsPage />} />

          <Route
            path="admin"
            element={
              <AdminOnlyRoute>
                <AdminPage />
              </AdminOnlyRoute>
            }
          />
        </Route>
      </Route>

      {/* Unknown routes */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}