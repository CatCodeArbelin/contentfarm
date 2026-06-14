const placeholders = [
  "Каркас интерфейса готов к развитию.",
  "Реальные API пока не подключены.",
  "Панель управления будет спроектирована отдельно.",
];

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.24),_transparent_36rem)] px-6 py-16">
      <section className="w-full max-w-3xl rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl shadow-blue-950/30 backdrop-blur md:p-12">
        <p className="mb-4 inline-flex rounded-full border border-blue-400/30 bg-blue-400/10 px-4 py-2 text-sm font-medium text-blue-200">
          Стартовая страница
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-white md:text-6xl">
          Contentfarm готовит новый интерфейс
        </h1>
        <p className="mt-6 text-lg leading-8 text-slate-300">
          Это временная русскоязычная заглушка для будущего фронтенда на Next.js App Router, TypeScript и Tailwind CSS.
        </p>
        <ul className="mt-8 grid gap-3 text-slate-200 md:grid-cols-3">
          {placeholders.map((item) => (
            <li key={item} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              {item}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
