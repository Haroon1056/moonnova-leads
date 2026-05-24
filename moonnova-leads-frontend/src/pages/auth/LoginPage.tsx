import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { APP_NAME } from "@/lib/constants";
import { useAuth } from "@/hooks/useAuth";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required")
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loginMutation, resendVerificationMutation } = useAuth();
  const [lastEmail, setLastEmail] = useState("");

  const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || "/dashboard";

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" }
  });

  async function onSubmit(values: LoginFormValues) {
    setLastEmail(values.email);
    await loginMutation.mutateAsync(values);
    navigate(from, { replace: true });
  }

  return (
    <Card>
      <CardHeader>
        <div className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-primarySoft text-primaryDark ring-1 ring-orange-200">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <CardTitle>Login to {APP_NAME}</CardTitle>
        <CardDescription>Access your lead generation workspace.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label>Email</Label>
            <Input type="email" placeholder="you@example.com" autoComplete="email" {...form.register("email")} />
            {form.formState.errors.email && <p className="mt-1 text-xs text-red-600">{form.formState.errors.email.message}</p>}
          </div>
          <div>
            <div className="flex items-center justify-between">
              <Label>Password</Label>
              <Link to="/auth/forgot-password" className="text-xs font-bold text-primaryDark hover:underline">Forgot password?</Link>
            </div>
            <Input type="password" placeholder="Enter password" autoComplete="current-password" {...form.register("password")} />
            {form.formState.errors.password && <p className="mt-1 text-xs text-red-600">{form.formState.errors.password.message}</p>}
          </div>
          {/* <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
            <AlertTriangle className="mr-1 inline h-4 w-4" /> If Chrome says “Change your password”, that is Google Password Manager detecting a weak/reused test password. Use a new unique password for this SaaS.
          </div> */}
          <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
            {loginMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Login
          </Button>
        </form>

        {lastEmail && (
          <Button
            variant="ghost"
            className="mt-3 w-full"
            disabled={resendVerificationMutation.isPending}
            onClick={() => resendVerificationMutation.mutate(lastEmail)}
          >
            {resendVerificationMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Resend verification email
          </Button>
        )}

        <p className="mt-6 text-center text-sm text-slate-500">
          Do not have an account? <Link to="/auth/register" className="font-bold text-primaryDark hover:underline">Create account</Link>
        </p>
      </CardContent>
    </Card>
  );
}
