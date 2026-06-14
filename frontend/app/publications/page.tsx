"use client";

import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";
import { getRussianErrorMessage, useGetPublications, type ApiStatus, type ListParams, type Publication } from "../../src/lib/api";

const statusOptions: Array<{ value: ApiStatus | ""; label: string }> = [
  { value: "", label: "Все статусы" },
  { value: "draft", label: "Черновик" },
  { value: "scheduled", label: "Запланирована" },
  { value: "processing", label: "В работе" },
  { value: "published", label: "Опубликована" },
  { value: "failed", label: "Ошибка публикации" },
  { value: "archived", label: "Архив" },
];

const statusPalette: Partial<Record<ApiStatus, string>> = {
  published: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
  processing: "border-cyan-300/30 bg-cyan-400/10 text-cyan-200",
  scheduled: "border-sky-300/30 bg-sky-400/10 text-sky-200",
  failed: "border-rose-300/30 bg-rose-400/10 text-rose-200",
  draft: "border-slate-300/30 bg-slate-400/10 text-slate-200",
  archived: "border-violet-300/30 bg-violet-400/10 text-violet-200",
};

function statusText(status: ApiStatus) {
  return statusOptions.find((item) => item.value === status)?.label ?? status;
}

function formatDate(value?: string | null) {
  if (!value) return "Не указано";
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function valueOrDash(value?: string | null) {
  return value?.trim() || "—";
}

function StatusBadge({ status }: { status: ApiStatus }) {
  return <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusPalette[status] ?? "border-white/15 bg-white/10 text-slate-200"}`}>{statusText(status)}</span>;
}

function SelectFilter({ label, value, onChange, options, allLabel }: { label: string; value: string; onChange: (value: string) => void; options: string[]; allLabel: string }) {
  return (
    <label className="grid gap-2 text-sm text-slate-300">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} className="rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-300/60">
        {options.map((option) => <option key={option || allLabel} value={option}>{option || allLabel}</option>)}
      </select>
    </label>
  );
}

function PublicationSkeleton() {
  return (
    <div className="animate-pulse rounded-3xl border border-white/10 bg-white/[0.06] p-5">
      <div className="flex flex-wrap items-center gap-3"><div className="h-7 w-36 rounded-full bg-slate-700/70" /><div className="h-4 w-14 rounded bg-slate-700/70" /></div>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => <div key={index} className="space-y-2"><div className="h-3 w-24 rounded bg-slate-800" /><div className="h-5 w-full rounded bg-slate-700/70" /></div>)}
      </div>
    </div>
  );
}

function ErrorDetails({ error }: { error?: string | null }) {
  if (!error) return <span className="text-slate-500">—</span>;
  return (
    <div className="rounded-2xl border border-rose-300/25 bg-rose-400/10 p-4 text-rose-100">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-rose-200/80">Ошибка публикации</p>
      <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6">{error}</p>
    </div>
  );
}

function CopyExportPathButton({ exportPath }: { exportPath?: string | null }) {
  const [copied, setCopied] = useState(false);
  const canCopy = Boolean(exportPath);

  async function handleCopy() {
    if (!exportPath) return;
    await navigator.clipboard.writeText(exportPath);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <button type="button" onClick={handleCopy} disabled={!canCopy} className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-sm font-bold text-cyan-100 transition hover:border-cyan-200/50 hover:bg-cyan-300/20 disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/[0.04] disabled:text-slate-500">
      {copied ? "Скопировано" : "Копировать export_path"}
    </button>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <div className="min-w-0 text-sm"><p className="text-slate-500">{label}</p><div className="mt-1 break-words font-medium text-slate-100">{children}</div></div>;
}

function PublicationCard({ publication }: { publication: Publication }) {
  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex flex-wrap items-center gap-2"><StatusBadge status={publication.status} /><span className="text-xs text-slate-500">Публикация #{publication.id}</span><span className="text-xs text-slate-500">Вариант #{publication.variant_id}</span></div>
        <CopyExportPathButton exportPath={publication.export_path} />
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Field label="status"><StatusBadge status={publication.status} /></Field>
        <Field label="platform">{valueOrDash(publication.platform)}</Field>
        <Field label="export_path"><code className="rounded-lg bg-slate-950/70 px-2 py-1 text-xs text-cyan-100">{valueOrDash(publication.export_path)}</code></Field>
        <Field label="message_id">{valueOrDash(publication.message_id)}</Field>
        <Field label="published_at">{formatDate(publication.published_at)}</Field>
        <Field label="error"><ErrorDetails error={publication.error} /></Field>
      </div>
    </article>
  );
}

export default function PublicationsPage() {
  const [status, setStatus] = useState("");
  const [platform, setPlatform] = useState("");
  const directoryQuery = useGetPublications({ limit: 200, offset: 0 });
  const filters = useMemo<ListParams>(() => ({ limit: 50, offset: 0, status: status as ApiStatus | undefined, platform }), [platform, status]);
  const publicationsQuery = useGetPublications(filters);
  const publications = publicationsQuery.data?.items ?? [];
  const allPublications = directoryQuery.data?.items ?? [];
  const platforms = ["", ...Array.from(new Set(allPublications.map((item) => item.platform).filter(Boolean))).sort()];

  return <main className="min-h-screen bg-slate-950 p-5 text-slate-100"><div className="mx-auto max-w-7xl space-y-5"><header className="rounded-3xl border border-white/10 bg-white/[0.06] p-6"><Link href="/" className="text-sm text-cyan-200">← На дашборд</Link><h1 className="mt-3 text-3xl font-bold text-white">Публикации</h1><p className="mt-2 text-slate-400">Отслеживайте статусы публикаций, экспортированные файлы, идентификаторы сообщений и ошибки отправки.</p></header><section className="grid gap-3 rounded-3xl border border-white/10 bg-white/[0.06] p-5 md:grid-cols-2"><label className="grid gap-2 text-sm text-slate-300">Статус<select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-300/60">{statusOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label><SelectFilter label="Платформа" value={platform} onChange={setPlatform} options={platforms} allLabel="Все платформы" /></section>{publicationsQuery.isLoading && <section className="space-y-3"><PublicationSkeleton /><PublicationSkeleton /><PublicationSkeleton /></section>}{publicationsQuery.error && <div className="rounded-3xl border border-rose-300/30 bg-rose-400/10 p-5 text-rose-100">Не удалось загрузить публикации: {getRussianErrorMessage(publicationsQuery.error)}</div>}<section className="space-y-3">{publications.map((publication) => <PublicationCard key={publication.id} publication={publication} />)}{!publicationsQuery.isLoading && !publicationsQuery.error && publications.length === 0 && <div className="rounded-3xl border border-dashed border-white/15 bg-slate-900/60 p-10 text-center"><p className="text-xl font-semibold text-white">Публикаций пока нет</p><p className="mt-2 text-slate-400">После экспорта или отправки материалов записи появятся здесь. Попробуйте изменить фильтры, если ожидаете увидеть существующие публикации.</p></div>}</section></div></main>;
}
