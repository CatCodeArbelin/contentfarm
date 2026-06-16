"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  getRussianErrorMessage,
  useDeduplicate,
  useGetRawItems,
  type ApiStatus,
  type ListParams,
  type RawItem,
} from "../../src/lib/api";
import { useToast } from "../../components/toast-provider";
import { addActionLogEntry } from "../../src/lib/action-log";
import {
  ActionButton,
  InlineNotice,
  OperationResult,
} from "../../components/action-ui";

import { statusText as ruStatusText } from "../../src/lib/ui-labels";
const statusOptions: Array<{ value: ApiStatus | ""; label: string }> = [
  { value: "", label: "Все статусы" },
  { value: "pending", label: "Ожидает" },
  { value: "processing", label: "В работе" },
  { value: "active", label: "Активен" },
  { value: "failed", label: "Ошибка" },
  { value: "archived", label: "Архив" },
];

function formatDate(value?: string | null) {
  if (!value) return "Дата не указана";
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusText(status: ApiStatus) {
  return statusOptions.find((item) => item.value === status)?.label ?? ruStatusText(status);
}

function isVisibleCount(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function deduplicateSummaryParts(data: {
  processed?: number;
  created?: number;
  linked?: number;
  already_linked?: number;
}) {
  return [
    isVisibleCount(data.processed)
      ? `Обработано материалов: ${data.processed}`
      : null,
    isVisibleCount(data.created)
      ? `Создано инфоповодов: ${data.created}`
      : null,
    isVisibleCount(data.linked) ? `Связано материалов: ${data.linked}` : null,
    isVisibleCount(data.already_linked)
      ? `Уже было связано: ${data.already_linked}`
      : null,
  ].filter(Boolean) as string[];
}

function SelectFilter({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="grid gap-2 text-sm text-slate-300">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-300/60"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option || "Все"}
          </option>
        ))}
      </select>
    </label>
  );
}

function RawItemCard({ item }: { item: RawItem }) {
  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-amber-300/30 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-100">
              {statusText(item.status)}
            </span>
            <span className="text-xs text-slate-500">
              #{item.id} · источник #{item.source_id}
            </span>
          </div>
          <h2 className="mt-3 line-clamp-2 text-lg font-semibold text-white">
            {item.title || "Без заголовка"}
          </h2>
          <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-400">
            {item.content || "Текст материала отсутствует."}
          </p>
          <a
            href={item.url}
            target="_blank"
            rel="noreferrer"
            className="mt-3 block break-all text-sm text-cyan-200 hover:text-cyan-100"
          >
            {item.url}
          </a>
        </div>
        <div className="grid gap-3 text-sm sm:grid-cols-2 xl:w-80">
          <div>
            <p className="text-slate-500">Площадка</p>
            <p className="mt-1 text-slate-100">
              {item.platform || "Не указана"}
            </p>
          </div>
          <div>
            <p className="text-slate-500">Язык</p>
            <p className="mt-1 text-slate-100">{item.language}</p>
          </div>
          <div>
            <p className="text-slate-500">Тема</p>
            <p className="mt-1 text-slate-100">{item.topic || "Не указана"}</p>
          </div>
          <div>
            <p className="text-slate-500">Создан</p>
            <p className="mt-1 text-slate-100">{formatDate(item.created_at)}</p>
          </div>
        </div>
      </div>
    </article>
  );
}

export default function RawItemsPage() {
  const { showToast } = useToast();
  const [status, setStatus] = useState<ApiStatus | "">("pending");
  const [platform, setPlatform] = useState("");
  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState("");
  const directoryQuery = useGetRawItems({ limit: 200, offset: 0 });
  const filters = useMemo<ListParams>(
    () => ({
      limit: 50,
      offset: 0,
      status: status || undefined,
      platform,
      topic,
      language,
    }),
    [language, platform, status, topic],
  );
  const rawItemsQuery = useGetRawItems(filters);
  const deduplicate = useDeduplicate({
    onSuccess: (data) => {
      const summary = deduplicateSummaryParts(data);
      addActionLogEntry({
        action: `Дедуплицировано ${data.processed ?? 0} материалов`,
        result: summary.length > 0 ? summary.join(". ") : "Операция завершена, инфоповоды обновлены.",
        href: "/news-events",
        linkLabel: "Проверить инфоповоды",
        tone: "success",
      });
      showToast({
        title: "Дедупликация завершена",
        description:
          summary.length > 0
            ? summary.join(". ")
            : "Операция завершена, список материалов и инфоповодов обновлён.",
        kind: "success",
      });
    },
    onError: (error) => {
      addActionLogEntry({
        action: "Дедупликация материалов",
        result: `Ошибка: ${getRussianErrorMessage(error)}`,
        href: "/raw-items",
        linkLabel: "Проверить сырьё",
        tone: "error",
      });
      showToast({
        title: "Не удалось выполнить дедупликацию",
        description: getRussianErrorMessage(error),
        kind: "error",
      });
    },
  });
  const allItems = directoryQuery.data?.items ?? [];
  const rawItems = rawItemsQuery.data?.items ?? [];
  const platforms = [
    "",
    ...Array.from(
      new Set(
        allItems.map((item) => item.platform).filter(Boolean) as string[],
      ),
    ).sort(),
  ];
  const topics = [
    "",
    ...Array.from(
      new Set(allItems.map((item) => item.topic).filter(Boolean) as string[]),
    ).sort(),
  ];
  const languages = [
    "",
    ...Array.from(
      new Set(allItems.map((item) => item.language).filter(Boolean)),
    ).sort(),
  ];
  const pendingCount = allItems.filter(
    (item) => item.status === "pending",
  ).length;
  const canDeduplicate = pendingCount > 0;
  const deduplicateResultParts = deduplicate.data
    ? deduplicateSummaryParts(deduplicate.data)
    : [];

  return (
    <main className="min-h-screen bg-slate-950 p-5 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="rounded-3xl border border-white/10 bg-white/[0.06] p-6">
          <Link href="/" className="text-sm text-cyan-200">
            ← На дашборд
          </Link>
          <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">Сырые материалы</h1>
              <p className="mt-2 text-slate-400">
                Сырые материалы из RSS и других источников с фильтрами
                обработки.
              </p>
            </div>
            <div className="space-y-2 lg:max-w-md">
              <ActionButton
                variant="primary"
                disabled={!canDeduplicate || deduplicate.isPending}
                isLoading={deduplicate.isPending}
                loadingText="Выполняется дедупликация…"
                onClick={() => {
                  showToast({
                    title: "Выполняется…",
                    description:
                      "Ищем дубли и связываем сырые материалы с инфоповодами.",
                    kind: "loading",
                  });
                  deduplicate.mutate(100);
                }}
              >
                Дедуплицировать ожидающие
              </ActionButton>
              {canDeduplicate ? (
                <InlineNotice tone="info">
                  Действие доступно: {pendingCount} ожидающих материалов будут
                  проверены на дубли.
                </InlineNotice>
              ) : (
                <InlineNotice tone="warning">
                  <p>Нет ожидающих сырых материалов для дедупликации</p>
                  <Link
                    href="/sources"
                    className="mt-2 inline-flex font-semibold text-amber-50 underline decoration-amber-200/50 underline-offset-4 hover:text-white"
                  >
                    Собрать RSS
                  </Link>
                </InlineNotice>
              )}
            </div>
          </div>
          {deduplicate.isPending && (
            <div className="mt-4">
              <InlineNotice tone="info">
                Выполняется дедупликация… Ищем дубли, создаём инфоповоды и
                связываем с ними сырые материалы.
              </InlineNotice>
            </div>
          )}
          {deduplicate.isSuccess && (
            <div className="mt-4">
              <OperationResult
                title="Дедупликация завершена"
                summary={
                  <div className="space-y-3">
                    {deduplicateResultParts.length > 0 ? (
                      <ul className="list-inside list-disc space-y-1">
                        {deduplicateResultParts.map((part) => (
                          <li key={part}>{part}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>
                        Операция завершена, список материалов и инфоповодов
                        обновлён.
                      </p>
                    )}
                    <Link
                      href="/news-events"
                      className="inline-flex font-semibold text-emerald-50 underline decoration-emerald-200/50 underline-offset-4 hover:text-white"
                    >
                      Открыть инфоповоды
                    </Link>
                  </div>
                }
              />
            </div>
          )}
          {deduplicate.isError && (
            <div className="mt-4">
              <InlineNotice tone="error">
                Не удалось выполнить дедупликацию:{" "}
                {getRussianErrorMessage(deduplicate.error)}
              </InlineNotice>
            </div>
          )}
        </header>
        <section className="grid gap-3 rounded-3xl border border-white/10 bg-white/[0.06] p-5 md:grid-cols-4">
          <label className="grid gap-2 text-sm text-slate-300">
            Статус
            <select
              value={status}
              onChange={(event) =>
                setStatus(event.target.value as ApiStatus | "")
              }
              className="rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-300/60"
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <SelectFilter
            label="Площадка"
            value={platform}
            onChange={setPlatform}
            options={platforms}
          />
          <SelectFilter
            label="Тема"
            value={topic}
            onChange={setTopic}
            options={topics}
          />
          <SelectFilter
            label="Язык"
            value={language}
            onChange={setLanguage}
            options={languages}
          />
        </section>
        {rawItemsQuery.isLoading && (
          <div className="rounded-3xl border border-white/10 bg-slate-900 p-5 text-slate-300">
            Загружаем сырые материалы…
          </div>
        )}
        {rawItemsQuery.error && (
          <div className="rounded-3xl border border-rose-300/30 bg-rose-400/10 p-5 text-rose-100">
            Не удалось загрузить сырые материалы:{" "}
            {getRussianErrorMessage(rawItemsQuery.error)}
          </div>
        )}
        <section className="space-y-3">
          {rawItems.map((item) => (
            <RawItemCard key={item.id} item={item} />
          ))}
          {!rawItemsQuery.isLoading && rawItems.length === 0 && (
            <div className="rounded-3xl border border-dashed border-white/15 bg-slate-900/60 p-8 text-center text-slate-400">
              По выбранным фильтрам сырых материалов нет.
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
