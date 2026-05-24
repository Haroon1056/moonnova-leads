import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Mail } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { APP_NAME } from "@/lib/constants";
import { useAuth } from "@/hooks/useAuth";

const registerSchema = z.object({
  full_name: z.string().min(2, "Full name is required"),
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  password2: z.string().min(8, "Confirm your password")
}).refine((data) => data.password === data.password2, {
  message: "Passwords do not match",
  path: ["password2"]
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const { registerMutation, resendVerificationMutation } = useAuth();
  const [registeredEmail, setRegisteredEmail] = useState("");

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name: "", email: "", password: "", password2: "" }
  });

  async function onSubmit(values: RegisterFormValues) {
    await registerMutation.mutateAsync({
      full_name: values.full_name,
      email: values.email,
      password: values.password
    });
    setRegisteredEmail(values.email);
  }

  if (registeredEmail) {
    return (
      <Card>
        <CardHeader className="text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-green-50 text-green-700 ring-1 ring-green-200">
            <Mail className="h-7 w-7" />
          </div>
          <CardTitle>Check your email</CardTitle>
          <CardDescription>
            We created your account and sent a verification link to <b>{registeredEmail}</b>.
            Open that link to activate your account before login.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            variant="outline"
            className="w-full"
            disabled={resendVerificationMutation.isPending}
            onClick={() => resendVerificationMutation.mutate(registeredEmail)}
          >
            {resendVerificationMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Resend Verification Email
          </Button>
          <Link to="/auth/login"><Button className="w-full">Back to Login</Button></Link>
          <p className="text-xs leading-5 text-slate-500">
            Note: email sending also requires SMTP settings in the Django backend. Set DEFAULT_FROM_EMAIL, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, and FRONTEND_URL.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create your {APP_NAME} account</CardTitle>
        <CardDescription>Start finding, enriching, and exporting leads professionally.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label>Full Name</Label>
            <Input placeholder="Hafiz Sajid" autoComplete="name" {...form.register("full_name")} />
            {form.formState.errors.full_name && <p className="mt-1 text-xs text-red-600">{form.formState.errors.full_name.message}</p>}
          </div>
          <div>
            <Label>Email</Label>
            <Input type="email" placeholder="you@example.com" autoComplete="email" {...form.register("email")} />
            {form.formState.errors.email && <p className="mt-1 text-xs text-red-600">{form.formState.errors.email.message}</p>}
          </div>
          <div>
            <Label>Password</Label>
            <Input type="password" placeholder="Minimum 8 characters" autoComplete="new-password" {...form.register("password")} />
            {form.formState.errors.password && <p className="mt-1 text-xs text-red-600">{form.formState.errors.password.message}</p>}
          </div>
          <div>
            <Label>Confirm Password</Label>
            <Input type="password" placeholder="Confirm password" autoComplete="new-password" {...form.register("password2")} />
            {form.formState.errors.password2 && <p className="mt-1 text-xs text-red-600">{form.formState.errors.password2.message}</p>}
          </div>
          {/* <div className="rounded-2xl border border-borderSoft bg-cardSoft p-3 text-xs leading-5 text-slate-600">
            <CheckCircle2 className="mr-1 inline h-4 w-4 text-green-700" /> Use a unique password for testing. Chrome's breach warning comes from Google Password Manager, not from MoonNova.
          </div> */}
          <Button type="submit" className="w-full" disabled={registerMutation.isPending}>
            {registerMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create Account
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account? <Link to="/auth/login" className="font-bold text-primaryDark hover:underline">Login</Link>
        </p>
      </CardContent>
    </Card>
  );
}
