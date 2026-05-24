import { useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export function VerifyEmailPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { verifyEmailMutation } = useAuth();

  useEffect(() => {
    if (token && !verifyEmailMutation.isPending && !verifyEmailMutation.isSuccess && !verifyEmailMutation.isError) {
      verifyEmailMutation.mutate(token);
    }
  }, [token, verifyEmailMutation]);

  useEffect(() => {
    if (verifyEmailMutation.isSuccess) {
      const timer = window.setTimeout(() => navigate("/dashboard", { replace: true }), 1200);
      return () => window.clearTimeout(timer);
    }
  }, [verifyEmailMutation.isSuccess, navigate]);

  const state = !token ? "missing" : verifyEmailMutation.isSuccess ? "success" : verifyEmailMutation.isError ? "error" : "loading";

  return (
    <Card>
      <CardHeader className="text-center">
        <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-cardSoft ring-1 ring-borderSoft">
          {state === "success" && <CheckCircle2 className="h-7 w-7 text-green-700" />}
          {state === "error" || state === "missing" ? <XCircle className="h-7 w-7 text-red-700" /> : null}
          {state === "loading" && <Loader2 className="h-7 w-7 animate-spin text-primary" />}
        </div>
        <CardTitle>
          {state === "success" && "Email verified"}
          {state === "loading" && "Verifying your email"}
          {state === "error" && "Verification failed"}
          {state === "missing" && "Verification token missing"}
        </CardTitle>
        <CardDescription>
          {state === "success" && "Your account is active. Redirecting to dashboard..."}
          {state === "loading" && "Please wait while we activate your account."}
          {state === "error" && "This link may be expired or already used. Request a new verification email from the login page."}
          {state === "missing" && "Open the full verification link from your email."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Link to="/auth/login"><Button className="w-full">Go to Login</Button></Link>
      </CardContent>
    </Card>
  );
}
