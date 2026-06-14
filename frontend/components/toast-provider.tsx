"use client";

import { createContext, type ReactNode, useContext, useMemo, useState } from "react";

type ToastKind = "info" | "success" | "error" | "loading";

type Toast = {
  id: number;
  title: string;
  description: string;
  kind?: ToastKind;
};

type ToastContextValue = {
  showToast: (toast: Omit<Toast, "id">) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error("useToast должен использоваться внутри ToastProvider");
  }

  return context;
}

const dotStyles: Record<ToastKind, string> = {
  info: "bg-cyan-300 shadow-[0_0_16px_rgba(103,232,249,0.9)]",
  success: "bg-emerald-300 shadow-[0_0_16px_rgba(110,231,183,0.9)]",
  error: "bg-rose-300 shadow-[0_0_16px_rgba(253,164,175,0.9)]",
  loading: "bg-amber-300 shadow-[0_0_16px_rgba(252,211,77,0.9)]",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([
    {
      id: 1,
      title: "Интерфейс готов",
      description: "Уведомления покажут начало, завершение и результат операций.",
      kind: "info",
    },
  ]);

  const value = useMemo<ToastContextValue>(
    () => ({
      showToast: (toast) => {
        const id = Date.now();
        setToasts((current) => [...current, { ...toast, id }]);
        window.setTimeout(() => {
          setToasts((current) => current.filter((item) => item.id !== id));
        }, 4200);
      },
    }),
    [],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-6 right-6 z-50 flex w-[calc(100%-3rem)] max-w-sm flex-col gap-3">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="pointer-events-auto rounded-2xl border border-cyan-300/20 bg-slate-900/85 p-4 text-sm shadow-2xl shadow-cyan-950/40 backdrop-blur-xl"
          >
            <div className="flex items-start gap-3">
              <span className={`mt-1 h-2.5 w-2.5 rounded-full ${dotStyles[toast.kind ?? "info"]}`} />
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-white">{toast.title}</p>
                <p className="mt-1 text-slate-300">{toast.description}</p>
              </div>
              <button
                type="button"
                aria-label="Закрыть уведомление"
                onClick={() => setToasts((current) => current.filter((item) => item.id !== toast.id))}
                className="rounded-full px-2 text-slate-400 transition hover:bg-white/10 hover:text-white"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
