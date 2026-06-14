"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { getRussianErrorMessage, useCollectRss, useCreateSource, useGetSources, type ApiStatus, type Source } from "../../src/lib/api";
import { useToast } from "../../components/toast-provider";
import { ActionButton, InlineNotice, OperationResult } from "../../components/action-ui";

const statusLabels: Partial<Record<ApiStatus, string>> = { active: "Активен", pending: "Ожидает", failed: "Ошибка", archived: "Архив", draft: "Черновик", processing: "В работе" };
const initialForm = { name: "", url: "", language: "ru", topic: "", strategy: "" };

type FormState = typeof initialForm;
type FormErrors = Partial<Record<keyof FormState, string>>;

function formatDate(value?: string | null) {
  if (!value) return "Дата не указана";
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function statusText(status: ApiStatus) {
  return statusLabels[status] ?? status;
}

function validateForm(form: FormState) {
  const errors: FormErrors = {};
  if (!form.name.trim()) errors.name = "Укажите название источника.";
  if (!form.url.trim()) {
    errors.url = "Укажите ссылку на RSS-ленту.";
  } else {
    try {
      const url = new URL(form.url);
      if (!/^https?:$/.test(url.protocol)) errors.url = "Ссылка должна начинаться с http:// или https://.";
    } catch {
      errors.url = "Введите корректную ссылку на RSS-ленту.";
    }
  }
  if (!/^[a-zа-яё-]{2,16}$/i.test(form.language.trim())) errors.language = "Укажите язык от 2 до 16 символов, например ru или en.";
  return errors;
}

function SourceCard({ source, onCollect, disabled, isCollecting }: { source: Source; onCollect: (source: Source) => void; disabled: boolean; isCollecting: boolean }) {
  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2"><span className="rounded-full border border-emerald-300/30 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-200">{statusText(source.status)}</span><span className="text-xs text-slate-500">#{source.id}</span></div>
          <h2 className="mt-3 text-lg font-semibold text-white">{source.name}</h2>
          <a href={source.url} target="_blank" rel="noreferrer" className="mt-2 block break-all text-sm text-cyan-200 hover:text-cyan-100">{source.url}</a>
        </div>
        <ActionButton variant="primary" disabled={disabled} isLoading={isCollecting} loadingText="Собираем RSS…" onClick={() => onCollect(source)}>Собрать RSS</ActionButton>
      </div>
      <dl className="mt-5 grid gap-3 text-sm md:grid-cols-4"><div><dt className="text-slate-500">Платформа</dt><dd className="mt-1 text-slate-100">{source.platform}</dd></div><div><dt className="text-slate-500">Язык</dt><dd className="mt-1 text-slate-100">{source.language}</dd></div><div><dt className="text-slate-500">Тема</dt><dd className="mt-1 text-slate-100">{source.topic || "Не указана"}</dd></div><div><dt className="text-slate-500">Создан</dt><dd className="mt-1 text-slate-100">{formatDate(source.created_at)}</dd></div></dl>
    </article>
  );
}

export default function SourcesPage() {
  const { showToast } = useToast();
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState<FormErrors>({});
  const sourcesQuery = useGetSources({ limit: 100, offset: 0 });
  const createSource = useCreateSource({ onSuccess: () => { setForm(initialForm); setErrors({}); showToast({ title: "Источник добавлен", description: "RSS-источник сохранён и появился в списке." }); }, onError: (error) => showToast({ title: "Не удалось добавить источник", description: getRussianErrorMessage(error) }) });
  const [collectingSourceId, setCollectingSourceId] = useState<number | null>(null);
  const collectRss = useCollectRss({ onSuccess: (data) => showToast({ title: "Сбор RSS завершён", description: `Получено: ${data.fetched ?? 0}. Создано новых материалов: ${data.created ?? 0}. Пропущено: ${data.skipped ?? 0}.`, kind: "success" }), onError: (error) => showToast({ title: "Не удалось собрать RSS", description: getRussianErrorMessage(error), kind: "error" }), onSettled: () => setCollectingSourceId(null) });
  const sources = sourcesQuery.data?.items ?? [];
  const totalText = useMemo(() => `Показано источников: ${sources.length} из ${sourcesQuery.data?.total ?? sources.length}.`, [sources.length, sourcesQuery.data?.total]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validateForm(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) { showToast({ title: "Проверьте форму", description: "Исправьте ошибки в полях и попробуйте снова." }); return; }
    createSource.mutate({ name: form.name.trim(), url: form.url.trim(), platform: "rss", language: form.language.trim(), topic: form.topic.trim() || null, strategy: form.strategy.trim() || null, status: "active" });
  }

  return <main className="min-h-screen bg-slate-950 p-5 text-slate-100"><div className="mx-auto max-w-7xl space-y-5"><header className="rounded-3xl border border-white/10 bg-white/[0.06] p-6"><Link href="/" className="text-sm text-cyan-200">← На дашборд</Link><h1 className="mt-3 text-3xl font-bold text-white">Источники RSS</h1><p className="mt-2 text-slate-400">Добавляйте ленты, запускайте сбор и контролируйте список источников.</p></header><section className="grid gap-5 lg:grid-cols-[24rem_1fr]"><form onSubmit={submit} noValidate className="rounded-3xl border border-white/10 bg-white/[0.06] p-5"><h2 className="text-xl font-semibold text-white">Добавить RSS-источник</h2><p className="mt-1 text-sm text-slate-400">Все поля проверяются в браузере до отправки.</p><div className="mt-5 grid gap-4">{([{ key: "name", label: "Название", placeholder: "Например: Новости продукта" }, { key: "url", label: "RSS-ссылка", placeholder: "https://example.com/feed.xml" }, { key: "language", label: "Язык", placeholder: "ru" }, { key: "topic", label: "Тема", placeholder: "Опционально" }, { key: "strategy", label: "Стратегия", placeholder: "Опционально" }] as const).map((field) => <label key={field.key} className="grid gap-2 text-sm text-slate-300">{field.label}<input value={form[field.key]} onChange={(event) => setForm((current) => ({ ...current, [field.key]: event.target.value }))} placeholder={field.placeholder} className="rounded-2xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none placeholder:text-slate-600 focus:border-cyan-300/60" />{errors[field.key] && <span className="text-rose-200">{errors[field.key]}</span>}</label>)}</div><button type="submit" disabled={createSource.isPending} className="mt-5 w-full rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-200 disabled:bg-slate-600 disabled:text-slate-300">{createSource.isPending ? "Добавляем…" : "Добавить источник"}</button></form><section className="space-y-3"><div className="rounded-3xl border border-white/10 bg-white/[0.06] p-5"><h2 className="text-xl font-semibold text-white">Список источников</h2><p className="mt-1 text-sm text-slate-400">{totalText}</p></div>{sourcesQuery.isLoading && <div className="rounded-3xl border border-white/10 bg-slate-900 p-5 text-slate-300">Загружаем источники…</div>}{sourcesQuery.error && <div className="rounded-3xl border border-rose-300/30 bg-rose-400/10 p-5 text-rose-100">Не удалось загрузить источники: {getRussianErrorMessage(sourcesQuery.error)}</div>}{collectRss.isPending && <InlineNotice tone="info">Сбор RSS выполняется. Новые сырые материалы появятся после ответа API.</InlineNotice>}{collectRss.isSuccess && <OperationResult title="Сбор RSS завершён" summary={`Получено: ${collectRss.data.fetched ?? 0}. Создано новых материалов: ${collectRss.data.created ?? 0}. Пропущено: ${collectRss.data.skipped ?? 0}.`} />}{sources.map((source) => <SourceCard key={source.id} source={source} disabled={collectRss.isPending} isCollecting={collectingSourceId === source.id && collectRss.isPending} onCollect={(item) => { setCollectingSourceId(item.id); showToast({ title: "Выполняется…", description: `Собираем RSS из источника «${item.name}».`, kind: "loading" }); collectRss.mutate({ source_id: item.id }); }} />)}{!sourcesQuery.isLoading && sources.length === 0 && <div className="rounded-3xl border border-dashed border-white/15 bg-slate-900/60 p-8 text-center text-slate-400">Источников пока нет. Добавьте первую RSS-ленту через форму.</div>}</section></section></div></main>;
}
