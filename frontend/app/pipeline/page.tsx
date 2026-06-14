"use client";

import Link from "next/link";
import { getRussianErrorMessage, useGetNewsEvents, useGetPublications, useGetRawItems, useGetSources, useGetVariants, type ApiStatus } from "../../src/lib/api";

type Tone = "done" | "next" | "wait" | "warn";
type Step = { id: string; title: string; status: string; tone: Tone; count: number; countLabel: string; action: string; href: string; hint: string; details: string; detailsLabel: string };

const toneClass: Record<Tone, string> = {
  done: "border-emerald-300/40 bg-emerald-400/10 text-emerald-100",
  next: "border-cyan-300/50 bg-cyan-400/10 text-cyan-100",
  wait: "border-slate-300/20 bg-slate-400/10 text-slate-200",
  warn: "border-amber-300/50 bg-amber-400/10 text-amber-100",
};

function num(value: number) {
  return value.toLocaleString("ru-RU");
}

function firstNext(steps: Step[]) {
  return steps.find((step) => step.tone === "next" || step.tone === "warn") ?? steps[0];
}

function StepCard({ step, index, active }: { step: Step; index: number; active: boolean }) {
  return (
    <article className={`relative rounded-3xl border p-5 shadow-2xl shadow-slate-950/30 ${active ? "border-cyan-300/70 bg-cyan-300/[0.12] ring-2 ring-cyan-300/30" : "border-white/10 bg-white/[0.06]"}`}>
      {active && <span className="absolute right-5 top-5 rounded-full bg-cyan-300 px-3 py-1 text-xs font-black uppercase tracking-[0.18em] text-slate-950">следующий шаг</span>}
      <div className="flex gap-4 pr-0 sm:pr-40">
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border text-lg font-black ${active ? "border-cyan-200 bg-cyan-300 text-slate-950" : "border-white/10 bg-slate-900 text-cyan-100"}`}>{index + 1}</span>
        <div>
          <h2 className="text-xl font-bold text-white">{step.title}</h2>
          <span className={`mt-3 inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${toneClass[step.tone]}`}>{step.status}</span>
        </div>
      </div>
      <div className="mt-5 rounded-2xl border border-white/10 bg-slate-950/45 p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Количество</p>
        <p className="mt-2 text-3xl font-black text-white">{num(step.count)}</p>
        <p className="mt-1 text-sm text-slate-400">{step.countLabel}</p>
      </div>
      <p className="mt-4 min-h-12 text-sm leading-6 text-slate-300">{step.hint}</p>
      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <Link href={step.href} className={`inline-flex flex-1 justify-center rounded-2xl px-4 py-3 text-center text-sm font-bold transition ${active ? "bg-cyan-300 text-slate-950 hover:bg-cyan-200" : "border border-white/10 bg-white/[0.06] text-slate-100 hover:bg-white/10"}`}>{step.action}</Link>
        <Link href={step.details} className="inline-flex flex-1 justify-center rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-center text-sm font-semibold text-cyan-100 transition hover:border-cyan-300/40 hover:bg-cyan-300/10">{step.detailsLabel}</Link>
      </div>
    </article>
  );
}

export default function PipelinePage() {
  const sources = useGetSources({ limit: 1, offset: 0 });
  const rawItems = useGetRawItems({ limit: 1, offset: 0 });
  const pendingRawItems = useGetRawItems({ limit: 1, offset: 0, status: "pending" as ApiStatus });
  const newsEvents = useGetNewsEvents({ limit: 1, offset: 0 });
  const variants = useGetVariants({ limit: 1, offset: 0 });
  const moderation = useGetVariants({ limit: 1, offset: 0, status: "pending_review" as ApiStatus });
  const approved = useGetVariants({ limit: 1, offset: 0, status: "approved" as ApiStatus });
  const publications = useGetPublications({ limit: 1, offset: 0 });
  const published = useGetPublications({ limit: 1, offset: 0, status: "published" as ApiStatus });
  const queries = [sources, rawItems, pendingRawItems, newsEvents, variants, moderation, approved, publications, published];
  const isLoading = queries.some((query) => query.isLoading);
  const error = queries.find((query) => query.error)?.error;

  const sourceCount = sources.data?.total ?? 0;
  const rawCount = rawItems.data?.total ?? 0;
  const pendingRawCount = pendingRawItems.data?.total ?? 0;
  const eventCount = newsEvents.data?.total ?? 0;
  const variantCount = variants.data?.total ?? 0;
  const moderationCount = moderation.data?.total ?? 0;
  const approvedCount = approved.data?.total ?? 0;
  const publicationCount = publications.data?.total ?? 0;
  const publishedCount = published.data?.total ?? 0;

  const steps: Step[] = [
    { id: "sources", title: "Источники", status: sourceCount ? "источники подключены" : "нужно добавить источники", tone: sourceCount ? "done" : "next", count: sourceCount, countLabel: "RSS-источников", action: "Добавить источник", href: "/sources", hint: "Добавьте RSS-ленту, язык, тему и стратегию. Это стартовая точка всего процесса.", details: "/sources", detailsLabel: "Подробно об источниках" },
    { id: "rss", title: "Сбор RSS", status: rawCount ? "материалы собраны" : sourceCount ? "готово к сбору" : "ждёт источники", tone: rawCount ? "done" : sourceCount ? "next" : "wait", count: rawCount, countLabel: "материалов после сбора", action: "Собрать RSS", href: "/sources", hint: "В разделе источников нажмите «Собрать RSS» у нужной ленты, чтобы получить новые материалы.", details: "/raw-items", detailsLabel: "Смотреть сырьё" },
    { id: "raw", title: "Сырые материалы", status: pendingRawCount ? "есть что обработать" : rawCount ? "сырьё есть" : "пусто", tone: pendingRawCount ? "next" : rawCount ? "done" : "wait", count: pendingRawCount || rawCount, countLabel: pendingRawCount ? "ожидают обработки" : "материалов всего", action: "Проверить материалы", href: "/raw-items", hint: "Просмотрите заголовки, ссылки и темы. Если всё корректно — переходите к дедупликации.", details: "/raw-items", detailsLabel: "Подробно о сырье" },
    { id: "dedupe", title: "Дедупликация", status: eventCount ? "дубли объединены" : pendingRawCount ? "можно запускать" : "ждёт сырьё", tone: eventCount ? "done" : pendingRawCount ? "next" : "wait", count: eventCount, countLabel: "инфоповодов создано", action: "Запустить дедупликацию", href: "/raw-items", hint: "Дедупликация группирует похожие материалы и создаёт инфоповоды для редактора.", details: "/news-events", detailsLabel: "Смотреть инфоповоды" },
    { id: "events", title: "Инфоповоды", status: eventCount ? "готовы к генерации" : "пока нет", tone: eventCount && !variantCount ? "next" : eventCount ? "done" : "wait", count: eventCount, countLabel: "инфоповодов", action: "Выбрать инфоповод", href: "/news-events", hint: "Оцените релевантность и риск, затем запустите генерацию у подходящего инфоповода.", details: "/news-events", detailsLabel: "Подробно об инфоповодах" },
    { id: "generation", title: "Генерация", status: variantCount ? "варианты созданы" : eventCount ? "готово к генерации" : "ждёт инфоповод", tone: variantCount ? "done" : eventCount ? "next" : "wait", count: variantCount, countLabel: "сгенерированных вариантов", action: "Сгенерировать текст", href: "/news-events", hint: "Генерация создаёт варианты текста. После этого оператор проверяет их на модерации.", details: "/variants", detailsLabel: "Смотреть варианты" },
    { id: "moderation", title: "Модерация", status: moderationCount ? "нужна проверка" : approvedCount ? "есть одобренные" : variantCount ? "нет ожидающих" : "ждёт генерацию", tone: moderationCount ? "warn" : approvedCount ? "done" : variantCount ? "next" : "wait", count: moderationCount || approvedCount || variantCount, countLabel: moderationCount ? "ожидают модерации" : approvedCount ? "одобрено" : "вариантов", action: "Открыть модерацию", href: "/variants", hint: "Проверьте текст, источники и риск. Одобренные варианты можно экспортировать или публиковать.", details: "/variants", detailsLabel: "Подробно о вариантах" },
    { id: "export", title: "Экспорт/публикация", status: publishedCount ? "публикации вышли" : approvedCount ? "готово к экспорту" : publicationCount ? "есть публикации" : "ждёт одобрение", tone: publishedCount ? "done" : approvedCount || publicationCount ? "next" : "wait", count: publicationCount || publishedCount, countLabel: "экспортов и публикаций", action: "Экспортировать/публиковать", href: approvedCount ? "/variants" : "/publications", hint: "Сделайте экспорт или публикацию и проверьте итоговый URL, файл или ошибку доставки.", details: "/publications", detailsLabel: "Подробно о публикациях" },
  ];
  const next = firstNext(steps);

  return (
    <main className="min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_18%_12%,rgba(34,211,238,0.18),transparent_28rem),radial-gradient(circle_at_84%_4%,rgba(124,58,237,0.22),transparent_30rem),linear-gradient(180deg,rgba(15,23,42,0),#020617_76%)]" />
      <div className="relative mx-auto max-w-7xl space-y-5 p-5">
        <header className="rounded-3xl border border-white/10 bg-white/[0.06] p-6 shadow-2xl shadow-slate-950/30">
          <Link href="/" className="text-sm text-cyan-200">← На дашборд</Link>
          <div className="mt-4 grid gap-5 lg:grid-cols-[1fr_22rem] lg:items-end">
            <div><p className="text-sm font-medium text-cyan-200">Главный рабочий экран оператора</p><h1 className="mt-2 text-3xl font-black tracking-tight text-white md:text-5xl">Конвейер Contentfarm</h1><p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">Вся цепочка от RSS-источника до публикации в одном месте: видно, что уже сделано, где сейчас находится процесс и какую кнопку нажать дальше.</p></div>
            <div className="rounded-3xl border border-cyan-300/30 bg-cyan-300/10 p-5"><p className="text-xs font-bold uppercase tracking-[0.22em] text-cyan-100">текущий следующий шаг</p><p className="mt-2 text-2xl font-black text-white">{steps.indexOf(next) + 1}. {next.title}</p><p className="mt-2 text-sm leading-6 text-cyan-50/80">{next.hint}</p><Link href={next.href} className="mt-4 inline-flex w-full justify-center rounded-2xl bg-cyan-300 px-4 py-3 text-sm font-bold text-slate-950 hover:bg-cyan-200">{next.action}</Link></div>
          </div>
        </header>
        {isLoading && <div className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 text-slate-300">Загружаем рабочий конвейер из backend…</div>}
        {error && <div className="rounded-3xl border border-rose-300/30 bg-rose-400/10 p-5 text-rose-100">Не удалось загрузить часть данных: {getRussianErrorMessage(error)}</div>}
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[['источников', sourceCount], ['сырых материалов', rawCount], ['вариантов текста', variantCount], ['опубликовано', publishedCount]].map(([label, value]) => <div key={label} className="rounded-3xl border border-white/10 bg-white/[0.06] p-5"><p className="text-3xl font-black text-white">{num(value as number)}</p><p className="mt-2 text-sm text-slate-400">{label}</p></div>)}
        </section>
        <section className="grid gap-5 xl:grid-cols-2">{steps.map((step, index) => <StepCard key={step.id} step={step} index={index} active={step.id === next.id} />)}</section>
      </div>
    </main>
  );
}
