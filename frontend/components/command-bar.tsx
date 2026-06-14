"use client";

import { useState } from "react";
import { useToast } from "./toast-provider";

export function CommandBar() {
  const { showToast } = useToast();

  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-center">
      <label className="relative block md:w-80">
        <span className="sr-only">Поиск</span>
        <input className="w-full rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60" placeholder="Найти материал, источник или задачу" />
      </label>
      <button
        type="button"
        onClick={() => showToast({ title: "Уведомление создано", description: "Это локальный UI-сигнал без обращения к бизнес API." })}
        className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm font-medium text-slate-200 transition hover:bg-white/10"
      >
        Показать уведомление
      </button>
      <button type="button" className="rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-200">
        Создать черновик
      </button>
    </div>
  );
}

export function ConfirmDialogPreview() {
  const [open, setOpen] = useState(true);

  if (!open) {
    return (
      <button type="button" onClick={() => setOpen(true)} className="mt-4 rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm font-medium text-slate-200">
        Показать диалог
      </button>
    );
  }

  return (
    <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/80 p-4">
      <p className="font-medium text-white">Подтвердить изменение статуса?</p>
      <p className="mt-2 text-sm text-slate-400">Это демонстрационный диалог без выполнения бизнес-действий.</p>
      <div className="mt-4 flex gap-3">
        <button type="button" onClick={() => setOpen(false)} className="flex-1 rounded-xl bg-white/10 px-3 py-2 text-sm text-white">
          Отмена
        </button>
        <button type="button" onClick={() => setOpen(false)} className="flex-1 rounded-xl bg-cyan-300 px-3 py-2 text-sm font-bold text-slate-950">
          Подтвердить
        </button>
      </div>
    </div>
  );
}
