import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({
  className,
  variant = "primary",
  size = "md",
  type = "button",
  ...props
}: ButtonProps) {
  const variants: Record<ButtonVariant, string> = {
    primary:
      "gradient-gold text-white shadow-glow hover:brightness-95 disabled:opacity-60",
    secondary:
      "border border-borderSoft bg-cardSoft text-slate-900 shadow-sm hover:bg-white disabled:opacity-60",
    outline:
      "border border-borderSoft bg-white/80 text-slate-800 shadow-sm hover:border-primary/40 hover:bg-primarySoft hover:text-primaryDark disabled:opacity-60",
    ghost:
      "text-slate-700 hover:bg-primarySoft hover:text-primaryDark disabled:opacity-60",
    danger:
      "bg-gradient-to-r from-red-700 to-rose-700 text-white shadow-md shadow-red-700/20 hover:brightness-95 disabled:opacity-60"
  };

  const sizes: Record<ButtonSize, string> = {
    sm: "h-9 px-3 text-xs",
    md: "h-10 px-4 text-sm",
    lg: "h-12 px-5 text-sm"
  };

  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-bold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-2 disabled:pointer-events-none",
        sizes[size],
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
