"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getActionLogEntries, subscribeActionLog, type ActionLogEntry, type ActionLogTone } from "../src/lib/action-log";

const toneClass: Record<ActionLogTone, string> = {
  success: "border-emerald-300/30 bg-emerald-400/10 text-emerald-100",
  warning: "border-amber-300/30 bg-amber-400/10 text-amber-100",
  error: "border-rose-300/30 bg-rose-400/10 text-rose-100",
  info: "border-cyan-300/30 bg-cyan-400/10 text-cyan-100",
};

function formatTime(value: string) {
  return new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date(value));
}

function RecentActionItem({ entry }: { entry: ActionLogEntry }) {
  return (
    <li className={`rounded-2xl border p-4 ${toneClass[entry.tone ?? "info"]}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <time className="text-xs font-semibold uppercase tracking-[0.18em] opacity-75">{formatTime(entry.timestamp)}</time>
          <p className="mt-2 font-semibold text-white">{entry.action}</p>
          <p className="mt-1 text-sm leading-6 opacity-90">{entry.result}</p>
        </div>
        {entry.href && (
          <Link href={entry.href} className="inline-flex shrink-0 rounded-xl border border-white/10 bg-slate-950/35 px-3 py-2 text-sm font-semibold text-cyan-50 hover:bg-slate-950/55">
            {entry.linkLabel ?? "Открыть"}
          </Link>
        )}
      </div>
    </li>
  );
}

export function RecentActions({ className = "" }: { className?: string }) {
  const [entries, setEntries] = useState<ActionLogEntry[]>([]);

  useEffect(() => {
    setEntries(getActionLogEntries());
    return subscribeActionLog(() => setEntries(getActionLogEntries()));
  }, []);

  return (
    <section className={`rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30 ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-white">Последние действия</h2>
          <p className="mt-1 text-sm text-slate-400">История действий текущей сессии в браузере.</p>
        </div>
        <span className="rounded-full border border-white/10 bg-slate-900/70 px-3 py-1 text-xs text-slate-300">{entries.length}</span>
      </div>
      <ol className="mt-4 space-y-3">
        {entries.length ? entries.slice(0, 8).map((entry) => <RecentActionItem key={entry.id} entry={entry} />) : <li className="rounded-2xl border border-dashed border-white/15 bg-slate-900/50 p-5 text-center text-sm text-slate-400">Пока действий нет. Запустите сбор RSS, дедупликацию, генерацию, одобрение или экспорт.</li>}
      </ol>
    </section>
  );
}
