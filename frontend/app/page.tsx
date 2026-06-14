import type { ReactNode } from "react";
import { CommandBar, ConfirmDialogPreview } from "../components/command-bar";

const navigation = [
  { label: "Обзор", active: true, count: "12" },
  { label: "Сбор данных", active: false, count: "4" },
  { label: "Черновики", active: false, count: "8" },
  { label: "Модерация", active: false, count: "3" },
  { label: "Публикации", active: false, count: "0" },
  { label: "Метрики", active: false, count: "—" },
];

const stats = [
  { label: "Материалов в очереди", value: "128", tone: "Готово" },
  { label: "Нужна проверка", value: "16", tone: "Внимание" },
  { label: "Источники онлайн", value: "24", tone: "Активно" },
];

const badges = ["Новый", "В работе", "Ожидает", "Готово", "Ошибка"];

const skeletonRows = Array.from({ length: 4 }, (_, index) => index);

function StatusBadge({ label }: { label: string }) {
  const palette: Record<string, string> = {
    Новый: "border-sky-300/30 bg-sky-400/10 text-sky-200",
    "В работе": "border-violet-300/30 bg-violet-400/10 text-violet-200",
    Ожидает: "border-amber-300/30 bg-amber-400/10 text-amber-200",
    Готово: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
    Ошибка: "border-rose-300/30 bg-rose-400/10 text-rose-200",
  };

  return <span className={`rounded-full border px-3 py-1 text-xs font-medium ${palette[label]}`}>{label}</span>;
}

function GlassCard({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-3xl border border-white/10 bg-white/[0.06] shadow-2xl shadow-slate-950/40 backdrop-blur-xl ${className}`}>{children}</section>;
}

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(34,211,238,0.22),transparent_28rem),radial-gradient(circle_at_82%_0%,rgba(124,58,237,0.24),transparent_30rem),linear-gradient(180deg,rgba(15,23,42,0),#020617_78%)]" />
      <div className="relative grid min-h-screen lg:grid-cols-[18rem_1fr]">
        <aside className="border-b border-white/10 bg-slate-950/70 p-5 backdrop-blur-xl lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-3 rounded-2xl border border-cyan-300/20 bg-cyan-300/10 p-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-300 text-lg font-black text-slate-950">CF</div>
            <div>
              <p className="font-semibold text-white">Contentfarm</p>
              <p className="text-xs text-slate-400">редакционная панель</p>
            </div>
          </div>
          <nav aria-label="Основная навигация" className="mt-8 space-y-2">
            {navigation.map((item) => (
              <a
                key={item.label}
                href="#"
                className={`flex items-center justify-between rounded-2xl px-4 py-3 text-sm transition ${
                  item.active ? "bg-white/10 text-white shadow-lg shadow-cyan-950/30" : "text-slate-400 hover:bg-white/[0.06] hover:text-white"
                }`}
              >
                <span>{item.label}</span>
                <span className="rounded-full bg-slate-900 px-2 py-0.5 text-xs text-slate-300">{item.count}</span>
              </a>
            ))}
          </nav>
          <div className="mt-8 rounded-3xl border border-white/10 bg-slate-900/70 p-4">
            <p className="text-sm font-medium text-white">Песочница</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">Действия согласования, экспорта и публикации здесь намеренно не реализованы.</p>
          </div>
        </aside>

        <section className="flex min-w-0 flex-col">
          <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/70 px-5 py-4 backdrop-blur-xl">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p className="text-sm text-cyan-200">Дашборд редакции</p>
                <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">Русскоязычный UI shell</h1>
              </div>
              <CommandBar />
            </div>
          </header>

          <div className="grid gap-5 p-5 xl:grid-cols-[1fr_22rem]">
            <div className="space-y-5">
              <div className="grid gap-5 md:grid-cols-3">
                {stats.map((stat) => (
                  <GlassCard key={stat.label} className="p-5">
                    <StatusBadge label={stat.tone === "Внимание" ? "Ожидает" : "Готово"} />
                    <p className="mt-6 text-3xl font-bold text-white">{stat.value}</p>
                    <p className="mt-2 text-sm text-slate-400">{stat.label}</p>
                  </GlassCard>
                ))}
              </div>

              <GlassCard className="p-5">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-white">Статусы материалов</h2>
                    <p className="mt-1 text-sm text-slate-400">Базовые бейджи дизайн-системы для будущих сценариев.</p>
                  </div>
                  <div className="flex flex-wrap gap-2">{badges.map((badge) => <StatusBadge key={badge} label={badge} />)}</div>
                </div>
              </GlassCard>

              <GlassCard className="p-5">
                <h2 className="text-xl font-semibold text-white">Загрузка очереди</h2>
                <div className="mt-5 space-y-3" aria-label="Скелетон загрузки">
                  {skeletonRows.map((row) => (
                    <div key={row} className="animate-pulse rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                      <div className="h-4 w-2/3 rounded-full bg-slate-700/80" />
                      <div className="mt-3 h-3 w-full rounded-full bg-slate-800" />
                    </div>
                  ))}
                </div>
              </GlassCard>
            </div>

            <div className="space-y-5">
              <GlassCard className="p-5 text-center">
                <div className="mx-auto grid h-16 w-16 place-items-center rounded-3xl border border-dashed border-cyan-200/30 bg-cyan-300/10 text-2xl">✦</div>
                <h2 className="mt-5 text-xl font-semibold text-white">Пока нет выбранного материала</h2>
                <p className="mt-2 text-sm leading-6 text-slate-400">Выберите карточку в очереди, чтобы увидеть предпросмотр, заметки редактора и историю изменений.</p>
                <button type="button" className="mt-5 rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm font-medium text-slate-200">Перейти к очереди</button>
              </GlassCard>

              <GlassCard className="p-5">
                <h2 className="text-xl font-semibold text-white">Диалог подтверждения</h2>
                <ConfirmDialogPreview />
              </GlassCard>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
