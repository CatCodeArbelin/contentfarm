"use client";

import Link from "next/link";
import { useState } from "react";
import { getRussianErrorMessage, useGenerateNewsEvent, useGetNewsEvents, type NewsEvent } from "../../src/lib/api";
import { ActionButton, InlineNotice, OperationResult } from "../../components/action-ui";
import { useToast } from "../../components/toast-provider";

function formatScore(score: number) {
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(score);
}

function riskLevelText(riskLevel?: string | null) {
  const labels: Record<string, string> = {
    low: "Низкий",
    medium: "Средний",
    high: "Высокий",
  };
  return labels[riskLevel ?? ""] ?? (riskLevel || "Не указан");
}

function sourceUrlText(sourceUrl?: string | null) {
  return sourceUrl || "Источник не указан";
}

function NewsEventCard({ event }: { event: NewsEvent }) {
  const { showToast } = useToast();
  const [successVariantIds, setSuccessVariantIds] = useState<number[]>([]);
  const generateMutation = useGenerateNewsEvent({
    onSuccess: (data) => {
      const ids = data.generated_variants.map((variant) => variant.id);
      setSuccessVariantIds(ids);
      showToast({ title: "Генерация завершена", description: `Создано вариантов: ${ids.length}.`, kind: "success" });
    },
    onError: (error) => showToast({ title: "Не удалось сгенерировать варианты", description: getRussianErrorMessage(error), kind: "error" }),
  });
  const isGenerating = generateMutation.isPending;

  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.24em] text-cyan-200">Инфоповод #{event.id}</p>
          <h2 className="mt-2 text-xl font-semibold text-white">{event.title}</h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">{event.summary}</p>
        </div>
<ActionButton variant="primary" isLoading={isGenerating} loadingText="Генерируем…" onClick={() => { showToast({ title: "Выполняется…", description: `Генерируем варианты для инфоповода #${event.id}.`, kind: "loading" }); generateMutation.mutate(event.id); }}>Сгенерировать</ActionButton>
      </div>

      <dl className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
          <dt className="text-xs text-slate-500">Оценка</dt>
          <dd className="mt-1 font-semibold text-slate-100">{formatScore(event.score)}</dd>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
          <dt className="text-xs text-slate-500">Уровень риска</dt>
          <dd className="mt-1 font-semibold text-slate-100">{riskLevelText(event.risk_level)}</dd>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
          <dt className="text-xs text-slate-500">Тема</dt>
          <dd className="mt-1 font-semibold text-slate-100">{event.topic || "Не указана"}</dd>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 md:col-span-2">
          <dt className="text-xs text-slate-500">Источник</dt>
          <dd className="mt-1 break-words text-sm font-semibold text-slate-100">
            {event.source_url ? (
              <a className="text-cyan-200 underline decoration-cyan-200/30 underline-offset-4 hover:text-cyan-100" href={event.source_url} target="_blank" rel="noreferrer">
                {sourceUrlText(event.source_url)}
              </a>
            ) : sourceUrlText(event.source_url)}
          </dd>
        </div>
      </dl>

      {isGenerating && <div className="mt-4"><InlineNotice tone="info">Идёт генерация вариантов. Кнопка отключена, изменения появятся после завершения.</InlineNotice></div>}
      {generateMutation.isSuccess && <div className="mt-4"><OperationResult title="Генерация завершена" summary={<>Создано вариантов: {successVariantIds.length}. <Link className="font-semibold underline underline-offset-4" href={successVariantIds.length === 1 ? `/variants/${successVariantIds[0]}` : "/variants"}>Перейти к вариантам</Link>.</>} /></div>}
      {generateMutation.isError && <div className="mt-4"><InlineNotice tone="error">Не удалось сгенерировать варианты: {getRussianErrorMessage(generateMutation.error)}</InlineNotice></div>}
    </article>
  );
}

export default function NewsEventsPage() {
  const newsEventsQuery = useGetNewsEvents({ limit: 50, offset: 0, sort_by: "score", sort_order: "desc" });
  const events = newsEventsQuery.data?.items ?? [];

  return (
    <main className="min-h-screen bg-slate-950 p-5 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="rounded-3xl border border-white/10 bg-white/[0.06] p-6">
          <Link href="/" className="text-sm text-cyan-200">← На дашборд</Link>
          <h1 className="mt-3 text-3xl font-bold text-white">Инфоповоды</h1>
          <p className="mt-2 text-slate-400">Выберите инфоповод, проверьте ключевые параметры и запустите генерацию вариантов.</p>
        </header>

        {newsEventsQuery.isLoading && <div className="rounded-3xl border border-white/10 bg-slate-900 p-5 text-slate-300">Загружаем инфоповоды…</div>}
        {newsEventsQuery.isError && <div className="rounded-3xl border border-rose-300/30 bg-rose-400/10 p-5 text-rose-100">Не удалось загрузить инфоповоды: {getRussianErrorMessage(newsEventsQuery.error)}</div>}

        <section className="space-y-4">
          {events.map((event) => <NewsEventCard key={event.id} event={event} />)}
          {!newsEventsQuery.isLoading && !newsEventsQuery.isError && events.length === 0 && <div className="rounded-3xl border border-dashed border-white/15 bg-slate-900/60 p-8 text-center text-slate-400">Инфоповоды пока не найдены.</div>}
        </section>
      </div>
    </main>
  );
}
