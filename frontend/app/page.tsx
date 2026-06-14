"use client";

import type { ReactNode } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CommandBar } from "../components/command-bar";
import {
  getRussianErrorMessage,
  useGetNewsEvents,
  useGetPublications,
  useGetRawItems,
  useGetSources,
  useGetVariants,
  type ApiStatus,
  type Publication,
  type Variant,
} from "../src/lib/api";

const statusLabels: Partial<Record<ApiStatus, string>> = {
  draft: "Черновики",
  needs_review: "Нужна проверка",
  pending: "Ожидают",
  active: "Активные",
  processing: "В работе",
  pending_review: "На модерации",
  approved: "Одобрены",
  rejected: "Отклонены",
  scheduled: "Запланированы",
  published: "Опубликованы",
  failed: "Ошибки",
  archived: "Архив",
};

const statusColors = ["#22d3ee", "#8b5cf6", "#f59e0b", "#10b981", "#f43f5e", "#64748b"];

function formatDate(value: string | null | undefined) {
  if (!value) return "Дата не указана";
  return new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function statusText(status: ApiStatus) {
  return statusLabels[status] ?? status;
}

function GlassCard({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-3xl border border-white/10 bg-white/[0.06] shadow-2xl shadow-slate-950/40 backdrop-blur-xl ${className}`}>{children}</section>;
}

function StatusBadge({ status }: { status: ApiStatus }) {
  const palette: Partial<Record<ApiStatus, string>> = {
    published: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
    approved: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
    active: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
    failed: "border-rose-300/30 bg-rose-400/10 text-rose-200",
    rejected: "border-rose-300/30 bg-rose-400/10 text-rose-200",
    pending: "border-amber-300/30 bg-amber-400/10 text-amber-200",
    pending_review: "border-amber-300/30 bg-amber-400/10 text-amber-200",
    scheduled: "border-sky-300/30 bg-sky-400/10 text-sky-200",
    draft: "border-slate-300/30 bg-slate-400/10 text-slate-200",
  };
  return <span className={`rounded-full border px-3 py-1 text-xs font-medium ${palette[status] ?? "border-violet-300/30 bg-violet-400/10 text-violet-200"}`}>{statusText(status)}</span>;
}

function LoadingBlock({ text = "Загружаем данные…" }: { text?: string }) {
  return <div className="animate-pulse rounded-2xl border border-white/10 bg-slate-900/70 p-4 text-sm text-slate-300">{text}</div>;
}

function ErrorBlock({ error }: { error: unknown }) {
  return <div className="rounded-2xl border border-rose-300/30 bg-rose-400/10 p-4 text-sm text-rose-100">Не удалось загрузить данные: {getRussianErrorMessage(error)}</div>;
}

function EmptyBlock({ text }: { text: string }) {
  return <div className="rounded-2xl border border-dashed border-white/15 bg-slate-900/50 p-5 text-center text-sm text-slate-400">{text}</div>;
}

function statusData(items: Array<{ status: ApiStatus }>) {
  return Object.entries(
    items.reduce<Partial<Record<ApiStatus, number>>>((acc, item) => {
      acc[item.status] = (acc[item.status] ?? 0) + 1;
      return acc;
    }, {}),
  ).map(([status, count]) => ({ status, label: statusText(status as ApiStatus), count }));
}

function StatusChart({ data }: { data: ReturnType<typeof statusData> }) {
  if (data.length === 0) return <EmptyBlock text="Пока нет данных для графика статусов." />;
  return (
    <div className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
          <CartesianGrid stroke="rgba(148,163,184,.16)" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: "#cbd5e1", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid rgba(255,255,255,.12)", borderRadius: 16 }} labelStyle={{ color: "#e2e8f0" }} />
          <Bar dataKey="count" radius={[10, 10, 0, 0]}>{data.map((_, i) => <Cell key={i} fill={statusColors[i % statusColors.length]} />)}</Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function LatestList<T extends Variant | Publication>({ title, items, getTitle }: { title: string; items: T[]; getTitle: (item: T) => string }) {
  return <GlassCard className="p-5"><h2 className="text-xl font-semibold text-white">{title}</h2><div className="mt-4 space-y-3">{items.length ? items.map((item) => <div key={item.id} className="rounded-2xl border border-white/10 bg-slate-900/60 p-4"><div className="flex items-start justify-between gap-3"><p className="line-clamp-2 text-sm font-medium text-white">{getTitle(item)}</p><StatusBadge status={item.status} /></div><p className="mt-2 text-xs text-slate-400">#{item.id} · {item.platform} · {formatDate(item.created_at)}</p></div>) : <EmptyBlock text="Пока ничего нет. Новые элементы появятся после обработки backend." />}</div></GlassCard>;
}

export default function Home() {
  const sources = useGetSources({ limit: 1 });
  const rawItems = useGetRawItems({ limit: 1 });
  const newsEvents = useGetNewsEvents({ limit: 1 });
  const latestVariants = useGetVariants({ limit: 5, offset: 0 });
  const latestPublications = useGetPublications({ limit: 5, offset: 0 });
  const variantsForChart = useGetVariants({ limit: 200, offset: 0 });
  const publicationsForChart = useGetPublications({ limit: 200, offset: 0 });
  const queries = [sources, rawItems, newsEvents, latestVariants, latestPublications, variantsForChart, publicationsForChart];
  const isLoading = queries.some((query) => query.isLoading);
  const firstError = queries.find((query) => query.error)?.error;
  const totals = [
    { label: "Всего источников", value: sources.data?.total ?? 0 },
    { label: "Сырые материалы", value: rawItems.data?.total ?? 0 },
    { label: "Новостные события", value: newsEvents.data?.total ?? 0 },
  ];
  const trendData = [
    { label: "Источники", value: sources.data?.total ?? 0 },
    { label: "Raw", value: rawItems.data?.total ?? 0 },
    { label: "События", value: newsEvents.data?.total ?? 0 },
    { label: "Варианты", value: variantsForChart.data?.total ?? 0 },
    { label: "Публикации", value: publicationsForChart.data?.total ?? 0 },
  ];

  return <main className="min-h-screen overflow-hidden bg-slate-950 text-slate-100"><div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(34,211,238,0.22),transparent_28rem),radial-gradient(circle_at_82%_0%,rgba(124,58,237,0.24),transparent_30rem),linear-gradient(180deg,rgba(15,23,42,0),#020617_78%)]" /><div className="relative min-h-screen"><header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/70 px-5 py-4 backdrop-blur-xl"><div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between"><div><p className="text-sm text-cyan-200">Дашборд редакции</p><h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">Contentfarm: состояние pipeline</h1></div><CommandBar /></div></header><div className="space-y-5 p-5">{isLoading && <LoadingBlock text="Загружаем сводку из backend…" />}{firstError && <ErrorBlock error={firstError} />}<div className="grid gap-5 md:grid-cols-3">{totals.map((stat) => <GlassCard key={stat.label} className="p-5"><p className="text-3xl font-bold text-white">{stat.value.toLocaleString("ru-RU")}</p><p className="mt-2 text-sm text-slate-400">{stat.label}</p></GlassCard>)}</div><div className="grid gap-5 xl:grid-cols-3"><GlassCard className="p-5 xl:col-span-1"><h2 className="text-xl font-semibold text-white">Общая динамика</h2><p className="mt-1 text-sm text-slate-400">Сравнение объёмов основных сущностей.</p><div className="mt-4 h-52"><ResponsiveContainer width="100%" height="100%"><AreaChart data={trendData}><Area type="monotone" dataKey="value" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.18} /><XAxis dataKey="label" tick={{ fill: "#cbd5e1", fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} /><Tooltip contentStyle={{ background: "#0f172a", border: "1px solid rgba(255,255,255,.12)", borderRadius: 16 }} /></AreaChart></ResponsiveContainer></div></GlassCard><GlassCard className="p-5"><h2 className="text-xl font-semibold text-white">Варианты по статусам</h2><StatusChart data={statusData(variantsForChart.data?.items ?? [])} /></GlassCard><GlassCard className="p-5"><h2 className="text-xl font-semibold text-white">Публикации по статусам</h2><StatusChart data={statusData(publicationsForChart.data?.items ?? [])} /></GlassCard></div><div className="grid gap-5 xl:grid-cols-[1fr_1fr_22rem]"><LatestList title="Последние варианты" items={latestVariants.data?.items ?? []} getTitle={(item) => item.title || item.lead || `Вариант ${item.id}`} /><LatestList title="Последние публикации" items={latestPublications.data?.items ?? []} getTitle={(item) => item.url || item.export_path || `Публикация ${item.id}`} /><GlassCard className="p-5"><h2 className="text-xl font-semibold text-white">Быстрые действия</h2><div className="mt-4 grid gap-3"><a className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-4 py-3 text-sm font-medium text-cyan-100" href="/sources">Добавить источник</a><a className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm font-medium text-slate-200" href="/news-events">Открыть инфоповоды</a><a className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm font-medium text-slate-200" href="/variants">Открыть модерацию</a><a className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm font-medium text-slate-200" href="/publications">Проверить публикации</a></div><p className="mt-4 text-sm leading-6 text-slate-400">Действия ведут в рабочие разделы и не заменяют backend-процессы.</p></GlassCard></div></div></div></main>;
}
