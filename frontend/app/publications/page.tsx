"use client";

import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";
import { EmptyState, InlineNotice } from "../../components/action-ui";
import { useToast } from "../../components/toast-provider";
import {
  getRussianErrorMessage,
  useGetPublications,
  useGetVariants,
  type ApiStatus,
  type ListParams,
  type Publication,
} from "../../src/lib/api";

import { statusText as ruStatusText } from "../../src/lib/ui-labels";
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
  return statusOptions.find((item) => item.value === status)?.label ?? ruStatusText(status);
}

function formatDate(value?: string | null) {
  if (!value) return "Не указано";
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
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
  return <div className="animate-pulse rounded-3xl border border-white/10 bg-white/[0.06] p-5"><div className="flex flex-wrap items-center gap-3"><div className="h-7 w-36 rounded-full bg-slate-700/70" /><div className="h-4 w-14 rounded bg-slate-700/70" /></div><div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }).map((_, index) => <div key={index} className="space-y-2"><div className="h-3 w-24 rounded bg-slate-800" /><div className="h-5 w-full rounded bg-slate-700/70" /></div>)}</div></div>;
}

function ErrorDetails({ error }: { error?: string | null }) {
  if (!error) return null;
  return (
    <div className="rounded-2xl border border-rose-300/40 bg-rose-500/15 p-4 text-rose-100 shadow-lg shadow-rose-950/20">
      <p className="text-sm font-bold text-rose-100">Публикация не завершилась</p>
      <p className="mt-1 text-sm text-rose-100/85">Сервер вернул ошибку. Проверьте настройки площадки или повторите действие после исправления причины.</p>
      <p className="mt-3 whitespace-pre-wrap break-words rounded-xl bg-slate-950/50 p-3 text-sm leading-6 text-rose-50">{error}</p>
    </div>
  );
}

function canOpenExportPath(exportPath?: string | null) {
  if (!exportPath) return false;
  return /^(https?:\/\/|\/)/i.test(exportPath);
}

function CopyExportPathButton({ exportPath }: { exportPath?: string | null }) {
  const { showToast } = useToast();
  const canCopy = Boolean(exportPath);
  async function handleCopy() {
    if (!exportPath) return;
    await navigator.clipboard.writeText(exportPath);
    showToast({ title: "Путь скопирован", description: exportPath, kind: "success" });
  }
  return <button type="button" onClick={handleCopy} disabled={!canCopy} className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-sm font-bold text-cyan-100 transition hover:border-cyan-200/50 hover:bg-cyan-300/20 disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/[0.04] disabled:text-slate-500">Скопировать путь</button>;
}

function OpenExportedFileAction({ exportPath }: { exportPath?: string | null }) {
  if (!exportPath) return null;
  if (!canOpenExportPath(exportPath)) return <span className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-semibold text-slate-500">Открыть экспортированный файл нельзя из браузера</span>;
  return <a href={exportPath} target="_blank" rel="noreferrer" className="rounded-2xl border border-emerald-300/20 bg-emerald-300/10 px-4 py-2 text-sm font-bold text-emerald-100 transition hover:border-emerald-200/50 hover:bg-emerald-300/20">Открыть экспортированный файл</a>;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <div className="min-w-0 text-sm"><p className="text-slate-500">{label}</p><div className="mt-1 break-words font-medium text-slate-100">{children}</div></div>;
}

function publicationTitle(publication: Publication, variantTitle?: string | null) {
  if (variantTitle?.trim()) return variantTitle;
  const parts = [publication.platform, formatDate(publication.published_at ?? publication.created_at), statusText(publication.status)].filter(Boolean);
  return parts.length ? parts.join(" · ") : `Публикация #${publication.id}`;
}

function MeaningBlock({ publication }: { publication: Publication }) {
  const isTelegram = publication.platform?.toLowerCase() === "telegram";
  const hasExport = Boolean(publication.export_path);
  if (publication.status === "failed") return <InlineNotice tone="error">Публикация не завершилась: материал не был успешно отправлен или сохранён. Подробности ошибки показаны ниже.</InlineNotice>;
  if (isTelegram && publication.status === "published") return <InlineNotice tone="success">Материал отправлен в Telegram{publication.message_id ? `, ID сообщения: ${publication.message_id}` : ""}.</InlineNotice>;
  if (hasExport) return <InlineNotice tone="success">Материал сохранён в файл. Путь можно скопировать или открыть, если браузеру доступен этот адрес.</InlineNotice>;
  return <InlineNotice tone="info">Запись показывает текущий этап публикации или экспорта. Когда файл будет готов, здесь появится путь.</InlineNotice>;
}

function PublicationCard({ publication, variantTitle }: { publication: Publication; variantTitle?: string | null }) {
  const title = publicationTitle(publication, variantTitle);
  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2"><StatusBadge status={publication.status} /><span className="text-xs text-slate-500">Публикация #{publication.id}</span><span className="text-xs text-slate-500">Вариант #{publication.variant_id}</span></div>
          <h2 className="mt-3 text-xl font-bold text-white">{title}</h2>
          <p className="mt-1 text-sm text-slate-400">{variantTitle ? "Связано с вариантом материала" : "Название варианта недоступно — показываем площадку, дату и статус."}</p>
        </div>
        <div className="flex flex-wrap gap-2 lg:max-w-xl lg:justify-end">
          <Link href={`/variants/${publication.variant_id}`} className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-2 text-sm font-bold text-slate-100 transition hover:border-white/25 hover:bg-white/10">Открыть вариант</Link>
          <CopyExportPathButton exportPath={publication.export_path} />
          <OpenExportedFileAction exportPath={publication.export_path} />
        </div>
      </div>
      <div className="mt-5"><p className="mb-2 text-sm font-semibold text-white">Что это значит</p><MeaningBlock publication={publication} /></div>
      {publication.status === "failed" && <div className="mt-4"><ErrorDetails error={publication.error} /></div>}
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Field label="Статус"><StatusBadge status={publication.status} /></Field>
        <Field label="Площадка">{valueOrDash(publication.platform)}</Field>
        <Field label="Путь к файлу"><code className="rounded-lg bg-slate-950/70 px-2 py-1 text-xs text-cyan-100">{valueOrDash(publication.export_path)}</code></Field>
        <Field label="ID сообщения">{valueOrDash(publication.message_id)}</Field>
        <Field label="Дата публикации">{formatDate(publication.published_at)}</Field>
        <Field label="Создано">{formatDate(publication.created_at)}</Field>
      </div>
    </article>
  );
}

export default function PublicationsPage() {
  const [status, setStatus] = useState("");
  const [platform, setPlatform] = useState("");
  const directoryQuery = useGetPublications({ limit: 200, offset: 0 });
  const variantsQuery = useGetVariants({ limit: 200, offset: 0 });
  const filters = useMemo<ListParams>(() => ({ limit: 50, offset: 0, status: status as ApiStatus | undefined, platform }), [platform, status]);
  const publicationsQuery = useGetPublications(filters);
  const publications = publicationsQuery.data?.items ?? [];
  const allPublications = directoryQuery.data?.items ?? [];
  const variantTitles = new Map((variantsQuery.data?.items ?? []).map((variant) => [variant.id, variant.title || variant.lead || `Вариант #${variant.id}`]));
  const platforms = ["", ...Array.from(new Set(allPublications.map((item) => item.platform).filter(Boolean))).sort()];

  return (
    <main className="min-h-screen bg-slate-950 p-5 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="rounded-3xl border border-white/10 bg-white/[0.06] p-6">
          <Link href="/" className="text-sm text-cyan-200">← На дашборд</Link>
          <h1 className="mt-3 text-3xl font-bold text-white">Публикации и экспорт</h1>
          <p className="mt-2 text-slate-400">Смотрите, какой вариант был отправлен или сохранён в файл, где лежит результат и что можно сделать дальше.</p>
        </header>
        <section className="grid gap-3 rounded-3xl border border-white/10 bg-white/[0.06] p-5 md:grid-cols-2">
          <label className="grid gap-2 text-sm text-slate-300">Статус<select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-300/60">{statusOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
          <SelectFilter label="Площадка" value={platform} onChange={setPlatform} options={platforms} allLabel="Все площадки" />
        </section>
        {publicationsQuery.isLoading && <section className="space-y-3"><PublicationSkeleton /><PublicationSkeleton /><PublicationSkeleton /></section>}
        {publicationsQuery.error && <div className="rounded-3xl border border-rose-300/30 bg-rose-400/10 p-5 text-rose-100">Не удалось загрузить публикации: {getRussianErrorMessage(publicationsQuery.error)}</div>}
        <section className="space-y-3">
          {publications.map((publication) => <PublicationCard key={publication.id} publication={publication} variantTitle={variantTitles.get(publication.variant_id)} />)}
          {!publicationsQuery.isLoading && !publicationsQuery.error && publications.length === 0 && (
            allPublications.length === 0 ? (
              <EmptyState
                title="Одобрите вариант и экспортируйте"
                description="Публикаций нет, потому что ни один вариант ещё не был экспортирован или отправлен. Перейдите к вариантам, откройте подходящий материал, одобрите его и нажмите кнопку экспорта или публикации."
                primaryAction={
                  <Link
                    href="/variants"
                    className="inline-flex items-center justify-center rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-200"
                  >
                    Перейти к вариантам
                  </Link>
                }
              />
            ) : (
              <EmptyState
                title="По фильтрам ничего не найдено"
                description="Публикации уже есть, но текущие фильтры скрыли список. Измените статус или площадку, чтобы увидеть экспортированные материалы."
                primaryAction={
                  <button
                    type="button"
                    onClick={() => { setStatus(""); setPlatform(""); }}
                    className="inline-flex items-center justify-center rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-200"
                  >
                    Сбросить фильтры
                  </button>
                }
              />
            )
          )}
        </section>
      </div>
    </main>
  );
}
