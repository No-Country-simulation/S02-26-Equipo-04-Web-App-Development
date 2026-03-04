import { useId } from "react";

type LogoVariant = "icon" | "compact" | "wordmark" | "wordmarkMono";

type LogoPalette = {
  gradientAStart: string;
  gradientAMid: string;
  gradientAEnd: string;
  gradientBStart: string;
  gradientBMid: string;
  gradientBEnd: string;
  nodeFill: string;
};

interface HaceloCortoLogoProps {
  variant?: LogoVariant;
  className?: string;
  title?: string;
  palette?: Partial<LogoPalette>;
}

const defaultPalette: LogoPalette = {
  gradientAStart: "var(--hc-logo-a-start, #89B4FA)",
  gradientAMid: "var(--hc-logo-a-mid, #89DCEB)",
  gradientAEnd: "var(--hc-logo-a-end, #CBA6F7)",
  gradientBStart: "var(--hc-logo-b-start, #F5C2E7)",
  gradientBMid: "var(--hc-logo-b-mid, #89DCEB)",
  gradientBEnd: "var(--hc-logo-b-end, #A6E3A1)",
  nodeFill: "var(--hc-logo-node, #1E1E2E)"
};

export function HaceloCortoLogo({
  variant = "compact",
  className,
  title = "Hacelo Corto",
  palette
}: HaceloCortoLogoProps) {
  const color = { ...defaultPalette, ...palette };
  const gradientA = useId();
  const gradientB = useId();

  if (variant === "icon") {
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 64 64"
        role="img"
        aria-label={title}
        className={className}
      >
        <defs>
          <linearGradient id={gradientA} x1="6" y1="6" x2="58" y2="58" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor={color.gradientAStart} />
            <stop offset="0.55" stopColor={color.gradientAMid} />
            <stop offset="1" stopColor={color.gradientAEnd} />
          </linearGradient>
          <linearGradient id={gradientB} x1="58" y1="6" x2="6" y2="58" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor={color.gradientBStart} />
            <stop offset="0.55" stopColor={color.gradientBMid} />
            <stop offset="1" stopColor={color.gradientBEnd} />
          </linearGradient>
        </defs>

        <circle cx="32" cy="32" r="24" fill="none" stroke={`url(#${gradientA})`} strokeWidth="5" />
        <path d="M29 23 L29 41 L43 32 Z" fill={`url(#${gradientB})`} />
        <path d="M19 45 L45 19" stroke={`url(#${gradientA})`} strokeWidth="4" strokeLinecap="round" />
        <circle cx="19" cy="45" r="3.5" fill={color.nodeFill} stroke={`url(#${gradientB})`} strokeWidth="2" />
        <circle cx="45" cy="19" r="3.5" fill={color.nodeFill} stroke={`url(#${gradientB})`} strokeWidth="2" />
      </svg>
    );
  }

  if (variant === "wordmarkMono") {
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 260 64"
        role="img"
        aria-label={title}
        className={className}
      >
        <g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="32" cy="32" r="22" strokeWidth="4" opacity="0.95" />
          <path d="M30 22 L30 42 L44 32 Z" fill="currentColor" stroke="none" opacity="0.95" />
          <path d="M18 46 L46 18" strokeWidth="3.5" opacity="0.9" />
          <circle cx="18" cy="46" r="3" fill="none" strokeWidth="3" />
          <circle cx="46" cy="18" r="3" fill="none" strokeWidth="3" />
        </g>

        <text
          x="72"
          y="38"
          fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial"
          fontSize="26"
          fontWeight="800"
          letterSpacing="-0.4"
          fill="currentColor"
        >
          Hacelo Corto
        </text>
      </svg>
    );
  }

  if (variant === "wordmark") {
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 260 64"
        role="img"
        aria-label={title}
        className={className}
      >
        <defs>
          <linearGradient id={gradientA} x1="10" y1="10" x2="54" y2="54" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor={color.gradientAStart} />
            <stop offset="0.55" stopColor={color.gradientAMid} />
            <stop offset="1" stopColor={color.gradientAEnd} />
          </linearGradient>
          <linearGradient id={gradientB} x1="58" y1="6" x2="6" y2="58" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor={color.gradientBStart} />
            <stop offset="0.55" stopColor={color.gradientBMid} />
            <stop offset="1" stopColor={color.gradientBEnd} />
          </linearGradient>
        </defs>

        <circle cx="32" cy="32" r="22" fill="none" stroke={`url(#${gradientA})`} strokeWidth="4" />
        <path d="M30 22 L30 42 L44 32 Z" fill={`url(#${gradientB})`} />
        <path d="M18 46 L46 18" stroke={`url(#${gradientA})`} strokeWidth="3.5" strokeLinecap="round" />
        <circle cx="18" cy="46" r="3" fill={color.nodeFill} stroke={`url(#${gradientB})`} strokeWidth="2.4" />
        <circle cx="46" cy="18" r="3" fill={color.nodeFill} stroke={`url(#${gradientB})`} strokeWidth="2.4" />

        <text
          x="72"
          y="38"
          fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial"
          fontSize="26"
          fontWeight="800"
          letterSpacing="-0.4"
          fill="currentColor"
        >
          Hacelo Corto
        </text>
      </svg>
    );
  }

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 140 64"
      role="img"
      aria-label={title}
      className={className}
    >
      <defs>
        <linearGradient id={gradientA} x1="10" y1="10" x2="54" y2="54" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor={color.gradientAStart} />
          <stop offset="0.55" stopColor={color.gradientAMid} />
          <stop offset="1" stopColor={color.gradientAEnd} />
        </linearGradient>
        <linearGradient id={gradientB} x1="54" y1="10" x2="10" y2="54" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor={color.gradientBStart} />
          <stop offset="0.55" stopColor={color.gradientBMid} />
          <stop offset="1" stopColor={color.gradientBEnd} />
        </linearGradient>
      </defs>

      <g transform="translate(6,6)">
        <circle cx="26" cy="26" r="20" fill="none" stroke={`url(#${gradientA})`} strokeWidth="4" />
        <path d="M24 17 L24 35 L36 26 Z" fill={`url(#${gradientB})`} />
        <path d="M14 38 L38 14" stroke={`url(#${gradientA})`} strokeWidth="3.5" strokeLinecap="round" />
      </g>

      <text
        x="66"
        y="40"
        fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial"
        fontSize="28"
        fontWeight="900"
        letterSpacing="-0.8"
        fill="currentColor"
      >
        H
        <tspan fill={`url(#${gradientB})`}>C</tspan>
      </text>
    </svg>
  );
}
