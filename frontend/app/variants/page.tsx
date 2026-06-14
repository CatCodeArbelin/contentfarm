"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  getRussianErrorMessage,
  useGetVariants,
  type ApiStatus,
  type ListParams,
  type Variant,
} from "../../src/lib/api";

const statusOptions: Array<{ value: ApiStatus | ""; label: string }> = [
  { value: "", label: "Все статусы" },
  { value: "draft", label: "Черновик" },
  { value: "pending_review", label: "На модерации" },
  { value: "approved", label: "Одобрен" },
  { value: "rejected", label: "Отклонён" },
  { value: "published", label: "Опубликован" },
  { value: "failed", label: "Ошибка" },
];

function statusText(status: ApiStatus) {
  return statusOptions.find((item) => item.value === status)?.label ?? status;
}

function formatDate(value?: string | null) {
  if (!value) return "Дата не указана";
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function StatusBadge({ status }: { status: ApiStatus }) {
  const palette: Partial<Record<ApiStatus, string>> = {
    approved: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
    published: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
    rejected: "border-rose-300/30 bg-rose-400/10 text-rose-200",
    failed: "border-rose-300/30 bg-rose-400/10 text-rose-200",
    pending_review: "border-amber-300/30 bg-amber-400/10 text-amber-200",
    draft: "border-slate-300/30 bg-slate-400/10 text-slate-200",
  };
  return (
    <span
      className={`rounded-full border px-3 py-1 text-xs font-medium ${palette[status] ?? "border-cyan-300/30 bg-cyan-400/10 text-cyan-200"}`}
    >
      {statusText(status)}
    </span>
  );
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

function VariantRow({ variant }: { variant: Variant }) {
  return (
    <Link
      href={`/variants/${variant.id}`}
      className="grid gap-4 rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30 transition hover:border-cyan-300/40 hover:bg-white/[0.09] xl:grid-cols-[1.4fr_.7fr_.7fr_.8fr_auto] xl:items-center"
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={variant.status} />
          <span className="text-xs text-slate-500">#{variant.id}</span>
        </div>
        <h2 className="mt-3 line-clamp-2 text-lg font-semibold text-white">
          {variant.title || variant.lead || "Без заголовка"}
        </h2>
        <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-400">
          {variant.lead || variant.body || variant.content}
        </p>
      </div>
      <div className="text-sm">
        <p className="text-slate-500">Платформа</p>
        <p className="mt-1 font-medium text-slate-100">{variant.platform}</p>
      </div>
      <div className="text-sm">
        <p className="text-slate-500">Тема</p>
        <p className="mt-1 font-medium text-slate-100">
          {variant.topic || "Не указана"}
        </p>
      </div>
      <div className="text-sm">
        <p className="text-slate-500">Создан</p>
        <p className="mt-1 font-medium text-slate-100">
          {formatDate(variant.created_at)}
        </p>
      </div>
      <span
        className={`rounded-2xl px-4 py-3 text-center text-sm font-bold ${variant.status === "approved" ? "border border-emerald-300/30 bg-emerald-400/10 text-emerald-100" : "bg-cyan-300 text-slate-950"}`}
      >
        {variant.status === "approved" ? "Уже одобрено" : "Открыть"}
      </span>
    </Link>
  );
}

export default function VariantsPage() {
  const [status, setStatus] = useState("");
  const [platform, setPlatform] = useState("");
  const [topic, setTopic] = useState("");
  const directoryQuery = useGetVariants({ limit: 200, offset: 0 });
  const filters = useMemo<ListParams>(
    () => ({
      limit: 50,
      offset: 0,
      status: status as ApiStatus | undefined,
      platform,
      topic,
    }),
    [platform, status, topic],
  );
  const variantsQuery = useGetVariants(filters);
  const variants = variantsQuery.data?.items ?? [];
  const allVariants = directoryQuery.data?.items ?? [];
  const platforms = [
    "",
    ...Array.from(
      new Set(allVariants.map((item) => item.platform).filter(Boolean)),
    ).sort(),
  ];
  const topics = [
    "",
    ...Array.from(
      new Set(
        allVariants.map((item) => item.topic).filter(Boolean) as string[],
      ),
    ).sort(),
  ];

  return (
    <main className="min-h-screen bg-slate-950 p-5 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="rounded-3xl border border-white/10 bg-white/[0.06] p-6">
          <Link href="/" className="text-sm text-cyan-200">
            ← На дашборд
          </Link>
          <h1 className="mt-3 text-3xl font-bold text-white">
            Сгенерированные варианты
          </h1>
          <p className="mt-2 text-slate-400">
            Список с гибридным card/table представлением и фильтрами модерации.
          </p>
        </header>
        <section className="grid gap-3 rounded-3xl border border-white/10 bg-white/[0.06] p-5 md:grid-cols-3">
          <label className="grid gap-2 text-sm text-slate-300">
            Статус
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
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
            label="Платформа"
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
        </section>
        {variantsQuery.isLoading && (
          <div className="rounded-3xl border border-white/10 bg-slate-900 p-5 text-slate-300">
            Загружаем варианты…
          </div>
        )}
        {variantsQuery.error && (
          <div className="rounded-3xl border border-rose-300/30 bg-rose-400/10 p-5 text-rose-100">
            Не удалось загрузить варианты:{" "}
            {getRussianErrorMessage(variantsQuery.error)}
          </div>
        )}
        <section className="space-y-3">
          {variants.map((variant) => (
            <VariantRow key={variant.id} variant={variant} />
          ))}
          {!variantsQuery.isLoading && variants.length === 0 && (
            <div className="rounded-3xl border border-dashed border-white/15 bg-slate-900/60 p-8 text-center text-slate-400">
              По выбранным фильтрам вариантов нет.
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
