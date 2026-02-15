import { ButtonHTMLAttributes } from "react";

type ButtonVariant = "cyan" | "violet" | "neutral";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const variantStyles: Record<ButtonVariant, string> = {
  cyan: "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan hover:bg-neon-cyan/25",
  violet: "border-neon-violet/45 bg-neon-violet/15 text-white hover:bg-neon-violet/25",
  neutral: "border-white/45 bg-white/5 text-white/60 hover:bg-white/10"
};

export function Button({ className, variant = "cyan", type = "button", ...props }: ButtonProps) {
  const classes = [
    "inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl border px-6 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
    variantStyles[variant],
    className
  ]
    .filter(Boolean)
    .join(" ");

  return <button type={type} className={classes} {...props} />;
}
