import type { ButtonHTMLAttributes, ReactNode } from "react";

type ActionButtonVariant = "primary" | "danger" | "neutral";

const buttonStyles: Record<ActionButtonVariant, string> = {
  primary: "bg-cyan-300 text-slate-950 hover:bg-cyan-200 disabled:bg-slate-600 disabled:text-slate-300",
  danger: "border border-rose-300/30 bg-rose-400/10 text-rose-100 hover:bg-rose-400/20 disabled:bg-rose-950/40 disabled:text-rose-200/60",
  neutral: "border border-white/10 bg-white/[0.06] text-slate-100 hover:bg-white/10 disabled:bg-white/[0.03] disabled:text-slate-500",
};

export function ActionButton({
  children,
  loadingText = "Выполняется…",
  isLoading = false,
  variant = "neutral",
  className = "",
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  loadingText?: string;
  isLoading?: boolean;
  variant?: ActionButtonVariant;
}) {
  return (
    <button
      type="button"
      disabled={disabled || isLoading}
      aria-busy={isLoading}
      className={`inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-70 ${buttonStyles[variant]} ${className}`}
      {...props}
    >
      {isLoading && <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" aria-hidden="true" />}
      <span>{isLoading ? loadingText : children}</span>
    </button>
  );
}

const noticeStyles = {
  info: "border-cyan-300/30 bg-cyan-400/10 text-cyan-100",
  success: "border-emerald-300/30 bg-emerald-400/10 text-emerald-100",
  error: "border-rose-300/30 bg-rose-400/10 text-rose-100",
  warning: "border-amber-300/30 bg-amber-400/10 text-amber-100",
} as const;

export function InlineNotice({ tone = "info", children }: { tone?: keyof typeof noticeStyles; children: ReactNode }) {
  return <div className={`rounded-2xl border p-4 text-sm leading-6 ${noticeStyles[tone]}`}>{children}</div>;
}

export function OperationResult({ tone = "success", title, summary }: { tone?: keyof typeof noticeStyles; title: string; summary: ReactNode }) {
  return (
    <InlineNotice tone={tone}>
      <p className="font-semibold text-white">{title}</p>
      <div className="mt-1">{summary}</div>
    </InlineNotice>
  );
}
