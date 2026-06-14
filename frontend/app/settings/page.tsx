"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getRussianErrorMessage, useHealthCheck } from "../../src/lib/api";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "Не задан";
const configuredFrontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL?.replace(/\/$/, "");
const configuredN8nUrl = process.env.NEXT_PUBLIC_N8N_URL?.replace(/\/$/, "") || "http://localhost:5678";
const nodeEnv = process.env.NODE_ENV || "неизвестно";

function statusLabel(status?: string) {
  if (!status) return "Нет ответа";
  if (["ok", "healthy", "up"].includes(status.toLowerCase())) return "Работает";
  return status;
}

function SettingCard({ title, value, description }: { title: string; value: string; description: string }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30">
      <p className="text-sm text-slate-400">{title}</p>
      <p className="mt-3 break-all text-lg font-semibold text-white">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
    </section>
  );
}

function ServiceLink({ href, title, description }: { href: string; title: string; description: string }) {
  return (
    <a className="rounded-3xl border border-white/10 bg-slate-900/70 p-5 transition hover:border-cyan-300/50 hover:bg-cyan-300/10" href={href} target={href.startsWith("http") ? "_blank" : undefined} rel={href.startsWith("http") ? "noreferrer" : undefined}>
      <span className="text-lg font-semibold text-white">{title}</span>
      <span className="mt-2 block text-sm leading-6 text-slate-400">{description}</span>
      <span className="mt-4 block break-all text-sm text-cyan-200">{href}</span>
    </a>
  );
}

export default function SettingsPage() {
  const [browserUrl, setBrowserUrl] = useState("");
  const health = useHealthCheck({ retry: 1, refetchInterval: 30_000 });
  const frontendUrl = configuredFrontendUrl || browserUrl || "Текущий адрес браузера";
  const docsUrl = apiBaseUrl === "Не задан" ? "#" : `${apiBaseUrl}/docs`;
  const healthTone = health.isSuccess ? "border-emerald-300/30 bg-emerald-400/10 text-emerald-100" : health.isLoading ? "border-amber-300/30 bg-amber-400/10 text-amber-100" : "border-rose-300/30 bg-rose-400/10 text-rose-100";
  const envRows = useMemo(
    () => [
      { label: "Режим сборки", value: nodeEnv },
      { label: "Backend API", value: apiBaseUrl },
      { label: "Frontend URL", value: frontendUrl },
      { label: "n8n URL", value: configuredN8nUrl },
    ],
    [frontendUrl],
  );

  useEffect(() => {
    setBrowserUrl(window.location.origin);
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 p-4 text-slate-100 sm:p-5">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 sm:p-6">
          <Link href="/" className="text-sm text-cyan-200">← На дашборд</Link>
          <div className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm text-cyan-200">Системная информация</p>
              <h1 className="mt-2 text-3xl font-bold text-white">Настройки</h1>
              <p className="mt-2 max-w-3xl text-slate-400">Проверка подключений и публичных адресов без сырого JSON: все ответы backend переведены в понятные статусы.</p>
            </div>
            <span className={`rounded-full border px-4 py-2 text-sm font-medium ${healthTone}`}>Backend: {health.isLoading ? "проверяем…" : health.isError ? "недоступен" : statusLabel(health.data?.status)}</span>
          </div>
        </header>

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <SettingCard title="API base URL" value={apiBaseUrl} description="Адрес используется frontend для запросов к FastAPI." />
          <SettingCard title="Backend health" value={health.isError ? getRussianErrorMessage(health.error) : statusLabel(health.data?.status)} description="Проверяется через /health и обновляется каждые 30 секунд." />
          <SettingCard title="Frontend" value={frontendUrl} description="Публичный адрес интерфейса из окружения или текущего окна браузера." />
          <SettingCard title="n8n" value={configuredN8nUrl} description="Ссылка на локальную панель автоматизаций и webhook-сценариев." />
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 sm:p-6">
          <h2 className="text-xl font-semibold text-white">Сводка окружения frontend</h2>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {envRows.map((row) => (
              <div key={row.label} className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                <p className="text-sm text-slate-400">{row.label}</p>
                <p className="mt-2 break-all font-medium text-white">{row.value}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 sm:p-6">
          <h2 className="text-xl font-semibold text-white">Быстрые ссылки</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <ServiceLink href={docsUrl} title="FastAPI docs" description="Интерактивная документация backend API." />
            <ServiceLink href={configuredN8nUrl} title="n8n" description="Автоматизации, webhook-и и интеграционные сценарии." />
            <ServiceLink href={frontendUrl} title="Frontend" description="Открыть пользовательский интерфейс Contentfarm." />
          </div>
        </section>
      </div>
    </main>
  );
}
