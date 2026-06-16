"use client";

import Link from "next/link";
import { useState } from "react";
import {
  getRussianErrorMessage,
  useGenerateNewsEvent,
  useGetNewsEvents,
  useGetVariants,
  type GenerateResponse,
  type NewsEvent,
  type Variant,
} from "../../src/lib/api";
import {
  ActionButton,
  InlineNotice,
  OperationResult,
} from "../../components/action-ui";
import { useToast } from "../../components/toast-provider";
import { addActionLogEntry } from "../../src/lib/action-log";

function formatScore(score: number) {
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(
    score,
  );
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

function formatPlatforms(platforms: string[]) {
  if (platforms.length === 0) {
    return "площадки не указаны";
  }
  return platforms.join(", ");
}

function platformsFromVariants(variants: Array<Pick<Variant, "platform">>) {
  return Array.from(
    new Set(
      variants
        .map((variant) => variant.platform)
        .filter((platform) => platform.trim().length > 0),
    ),
  );
}

function ollamaErrorDetails(error: unknown) {
  const message = getRussianErrorMessage(error);
  return message ? `Технические детали: ${message}` : null;
}

function GenerationResultBlock({
  count,
  platforms,
}: {
  count: number;
  platforms: string[];
}) {
  return (
    <OperationResult
      title="Варианты готовы"
      summary={
        <>
          Создано вариантов: {count}. Площадки: {formatPlatforms(platforms)}.{" "}
          <Link
            className="font-semibold underline underline-offset-4"
            href="/variants"
          >
            Открыть варианты
          </Link>
          .
        </>
      }
    />
  );
}

function NewsEventCard({
  event,
  variants,
}: {
  event: NewsEvent;
  variants: Variant[];
}) {
  const { showToast } = useToast();
  const [generatedResult, setGeneratedResult] = useState<{
    count: number;
    platforms: string[];
  } | null>(null);
  const generateMutation = useGenerateNewsEvent({
    onSuccess: (data: GenerateResponse) => {
      const platforms = platformsFromVariants(data.generated_variants);
      setGeneratedResult({
        count: data.generated_variants.length,
        platforms,
      });
      addActionLogEntry({
        action: "Сгенерированы варианты",
        result: `Создано вариантов: ${data.generated_variants.length}. Площадки: ${formatPlatforms(platforms)}.`,
        href: "/variants",
        linkLabel: "Открыть варианты",
        tone: "success",
      });
      showToast({
        title: "Генерация завершена",
        description: `Создано вариантов: ${data.generated_variants.length}. Площадки: ${formatPlatforms(platforms)}.`,
        kind: "success",
      });
    },
    onError: (error) => {
      addActionLogEntry({
        action: "Генерация вариантов",
        result: `Ошибка: ${getRussianErrorMessage(error)}`,
        href: "/news-events",
        linkLabel: "Открыть инфоповоды",
        tone: "error",
      });
      showToast({
        title: "Не удалось сгенерировать варианты",
        description: getRussianErrorMessage(error),
        kind: "error",
      });
    },
  });
  const existingVariants = variants.filter(
    (variant) => variant.generation_id === event.id,
  );
  const existingPlatforms = platformsFromVariants(existingVariants);
  const hasExistingVariants = existingVariants.length > 0;
  const isGenerating = generateMutation.isPending;
  const canGenerate =
    event.status !== "archived" &&
    event.status !== "failed" &&
    Boolean(event.title?.trim() || event.summary?.trim());
  const generateReason = hasExistingVariants
    ? `Для этого инфоповода уже есть варианты: ${existingVariants.length}. Площадки: ${formatPlatforms(existingPlatforms)}.`
    : canGenerate
      ? "Действие доступно: будет создан набор вариантов для модерации."
      : `Генерация недоступна: статус «${event.status}» или нет текста инфоповода.`;

  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.24em] text-cyan-200">
            Инфоповод #{event.id}
          </p>
          <h2 className="mt-2 text-xl font-semibold text-white">
            {event.title}
          </h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            {event.summary}
          </p>
        </div>
        <div className="space-y-2 lg:max-w-sm">
          {hasExistingVariants ? (
            <Link
              className="inline-flex items-center justify-center rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-200"
              href="/variants"
            >
              Открыть варианты
            </Link>
          ) : (
            <ActionButton
              variant="primary"
              disabled={!canGenerate || isGenerating}
              isLoading={isGenerating}
              loadingText="Генерируем варианты…"
              onClick={() => {
                if (generateMutation.isPending) {
                  showToast({
                    title: "Генерация уже выполняется",
                    description: `Дождитесь завершения генерации для инфоповода #${event.id}.`,
                    kind: "loading",
                  });
                  return;
                }
                setGeneratedResult(null);
                showToast({
                  title: "Генерируем варианты…",
                  description: `Генерация началась для инфоповода #${event.id}.`,
                  kind: "loading",
                });
                generateMutation.mutate(event.id);
              }}
            >
              Сгенерировать варианты
            </ActionButton>
          )}
          <InlineNotice
            tone={hasExistingVariants || canGenerate ? "info" : "warning"}
          >
            {generateReason}
          </InlineNotice>
        </div>
      </div>

      <dl className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
          <dt className="text-xs text-slate-500">Оценка</dt>
          <dd className="mt-1 font-semibold text-slate-100">
            {formatScore(event.score)}
          </dd>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
          <dt className="text-xs text-slate-500">Уровень риска</dt>
          <dd className="mt-1 font-semibold text-slate-100">
            {riskLevelText(event.risk_level)}
          </dd>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
          <dt className="text-xs text-slate-500">Тема</dt>
          <dd className="mt-1 font-semibold text-slate-100">
            {event.topic || "Не указана"}
          </dd>
        </div>
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 md:col-span-2">
          <dt className="text-xs text-slate-500">Источник</dt>
          <dd className="mt-1 break-words text-sm font-semibold text-slate-100">
            {event.source_url ? (
              <a
                className="text-cyan-200 underline decoration-cyan-200/30 underline-offset-4 hover:text-cyan-100"
                href={event.source_url}
                target="_blank"
                rel="noreferrer"
              >
                {sourceUrlText(event.source_url)}
              </a>
            ) : (
              sourceUrlText(event.source_url)
            )}
          </dd>
        </div>
      </dl>

      {isGenerating && (
        <div className="mt-4">
          <InlineNotice tone="info">
            Генерируем варианты… Генерация уже выполняется, повторный запуск
            недоступен.
          </InlineNotice>
        </div>
      )}
      {generatedResult && (
        <div className="mt-4">
          <GenerationResultBlock
            count={generatedResult.count}
            platforms={generatedResult.platforms}
          />
        </div>
      )}
      {hasExistingVariants && !generatedResult && (
        <div className="mt-4">
          <GenerationResultBlock
            count={existingVariants.length}
            platforms={existingPlatforms}
          />
        </div>
      )}
      {generateMutation.isError && (
        <div className="mt-4">
          <OperationResult
            tone="error"
            title="Не удалось сгенерировать варианты"
            summary={
              <>
                <p>Проверьте, что Ollama запущена и модель доступна.</p>
                {ollamaErrorDetails(generateMutation.error) && (
                  <details className="mt-2 text-rose-100/80">
                    <summary className="cursor-pointer font-semibold">
                      Технические детали
                    </summary>
                    <p className="mt-1">
                      {ollamaErrorDetails(generateMutation.error)}
                    </p>
                  </details>
                )}
              </>
            }
          />
        </div>
      )}
    </article>
  );
}

export default function NewsEventsPage() {
  const newsEventsQuery = useGetNewsEvents({
    limit: 50,
    offset: 0,
    sort_by: "score",
    sort_order: "desc",
  });
  const events = newsEventsQuery.data?.items ?? [];
  const variantsQuery = useGetVariants({ limit: 200, offset: 0 });
  const variants = variantsQuery.data?.items ?? [];

  return (
    <main className="min-h-screen bg-slate-950 p-5 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="rounded-3xl border border-white/10 bg-white/[0.06] p-6">
          <Link href="/" className="text-sm text-cyan-200">
            ← На дашборд
          </Link>
          <h1 className="mt-3 text-3xl font-bold text-white">Инфоповоды</h1>
          <p className="mt-2 text-slate-400">
            Выберите инфоповод, проверьте ключевые параметры и запустите
            генерацию вариантов.
          </p>
        </header>

        {newsEventsQuery.isLoading && (
          <div className="rounded-3xl border border-white/10 bg-slate-900 p-5 text-slate-300">
            Загружаем инфоповоды…
          </div>
        )}
        {newsEventsQuery.isError && (
          <div className="rounded-3xl border border-rose-300/30 bg-rose-400/10 p-5 text-rose-100">
            Не удалось загрузить инфоповоды:{" "}
            {getRussianErrorMessage(newsEventsQuery.error)}
          </div>
        )}

        <section className="space-y-4">
          {events.map((event) => (
            <NewsEventCard key={event.id} event={event} variants={variants} />
          ))}
          {!newsEventsQuery.isLoading &&
            !newsEventsQuery.isError &&
            events.length === 0 && (
              <div className="rounded-3xl border border-dashed border-white/15 bg-slate-900/60 p-8 text-center text-slate-400">
                Инфоповоды пока не найдены.
              </div>
            )}
        </section>
      </div>
    </main>
  );
}
