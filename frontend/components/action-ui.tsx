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

export function EmptyState({
  title,
  description,
  primaryAction,
  secondaryAction,
}: {
  title: string;
  description: ReactNode;
  primaryAction: ReactNode;
  secondaryAction?: ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-dashed border-cyan-200/30 bg-gradient-to-br from-cyan-400/10 via-white/[0.06] to-slate-900/80 p-8 text-center shadow-2xl shadow-cyan-950/20">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-200/30 bg-cyan-300/15 text-2xl" aria-hidden="true">
        →
      </div>
      <h2 className="mt-4 text-2xl font-bold text-white">{title}</h2>
      <div className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-300">
        {description}
      </div>
      <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
        {primaryAction}
        {secondaryAction}
      </div>
    </div>
  );
}
