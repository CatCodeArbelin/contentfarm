"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getRussianErrorMessage,
  useApproveVariant,
  useExportVariant,
  useGetVariant,
  usePublishTelegram,
  useRejectVariant,
  type ApiStatus,
  type ExportPlatform,
  type Variant,
} from "../../../src/lib/api";
import { useToast } from "../../../components/toast-provider";
import {
  ActionButton,
  InlineNotice,
  OperationResult,
} from "../../../components/action-ui";

const statusLabels: Partial<Record<ApiStatus, string>> = {
  draft: "Черновик",
  pending_review: "На модерации",
  approved: "Одобрен",
  rejected: "Отклонён",
  published: "Опубликован",
  failed: "Ошибка",
};
function statusText(status?: ApiStatus) {
  return status ? (statusLabels[status] ?? status) : "Неизвестно";
}
function formatDate(value?: string | null) {
  if (!value) return "Не указано";
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-slate-950/30">
      <h2 className="text-xl font-semibold text-white">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}
function MetadataPanel({ variant }: { variant: Variant }) {
  const rows = [
    ["ID", `#${variant.id}`],
    ["ID генерации", variant.generation_id],
    ["ID промпта", variant.prompt_id ?? "—"],
    ["Версия промпта", variant.prompt_version ?? "—"],
    ["Платформа", variant.platform],
    ["Стратегия", variant.strategy],
    ["Язык", variant.language],
    ["Тема", variant.topic ?? "—"],
    ["Риск", variant.risk_level ?? "—"],
    ["Оценка", variant.score ?? "—"],
    ["Создан", formatDate(variant.created_at)],
    ["Обновлён", formatDate(variant.updated_at)],
    ["Одобрил", variant.approved_by ?? "—"],
    ["Одобрен", formatDate(variant.approved_at)],
  ];
  return (
    <dl className="grid gap-3">
      {rows.map(([label, value]) => (
        <div
          key={label}
          className="flex items-start justify-between gap-4 rounded-2xl border border-white/10 bg-slate-900/60 p-3"
        >
          <dt className="text-sm text-slate-500">{label}</dt>
          <dd className="text-right text-sm font-medium text-slate-100">
            {String(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function variantActionState(variant: Variant) {
  const isApproved = variant.status === "approved";
  const isPublished = variant.status === "published";
  const isRejected = variant.status === "rejected";
  const canApprove = !isApproved && !isPublished && !isRejected;
  const canPublish = isApproved;
  return {
    isApproved,
    canApprove,
    canPublish,
    approveReason: isApproved
      ? "Уже одобрено"
      : isPublished
        ? "Вариант уже опубликован"
        : isRejected
          ? "Отклонённый вариант нельзя одобрить без повторной генерации"
          : "Можно одобрить после проверки текста.",
    publishReason: canPublish
      ? "Действие доступно: вариант одобрен."
      : `Сначала нужен статус «Одобрен». Сейчас: «${statusText(variant.status)}».`,
  };
}
function StatusTimeline({ variant }: { variant: Variant }) {
  const steps = [
    { label: "Создан", value: formatDate(variant.created_at), active: true },
    {
      label: "Обновлён",
      value: formatDate(variant.updated_at),
      active: Boolean(variant.updated_at),
    },
    {
      label: "Текущий статус",
      value: statusText(variant.status),
      active: true,
    },
    {
      label: "Одобрен",
      value: formatDate(variant.approved_at),
      active: Boolean(variant.approved_at),
    },
  ];
  return (
    <ol className="space-y-4">
      {steps.map((step) => (
        <li key={step.label} className="flex gap-3">
          <span
            className={`mt-1 h-3 w-3 rounded-full ${step.active ? "bg-cyan-300 shadow-[0_0_18px_rgba(103,232,249,.8)]" : "bg-slate-700"}`}
          />
          <div>
            <p className="font-medium text-white">{step.label}</p>
            <p className="text-sm text-slate-400">{step.value}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

export default function VariantDetailPage() {
  const params = useParams<{ id: string }>();
  const variantId = Number(params.id);
  const { showToast } = useToast();
  const variantQuery = useGetVariant(variantId);
  const approve = useApproveVariant({
    onSuccess: (data) =>
      showToast({
        title: "Вариант одобрен",
        description: `Статус варианта #${data.id} изменён на «${statusText(data.status)}».`,
        kind: "success",
      }),
    onError: (error) =>
      showToast({
        title: "Не удалось одобрить вариант",
        description: getRussianErrorMessage(error),
        kind: "error",
      }),
  });
  const reject = useRejectVariant({
    onSuccess: () =>
      showToast({
        title: "Вариант отклонён",
        description: "Данные обновлены через TanStack Query.",
      }),
    onError: (error) =>
      showToast({
        title: "Ошибка отклонения",
        description: getRussianErrorMessage(error),
      }),
  });
  const exportVariant = useExportVariant({
    onSuccess: (data) =>
      showToast({
        title: "Экспорт выполнен",
        description: `Создана публикация #${data.id}. Файл: ${data.export_path || "путь не вернулся от API"}.`,
        kind: "success",
      }),
    onError: (error) =>
      showToast({
        title: "Не удалось экспортировать",
        description: getRussianErrorMessage(error),
        kind: "error",
      }),
  });
  const publishTelegram = usePublishTelegram({
    onSuccess: () =>
      showToast({
        title: "Отправлено в Telegram",
        description: "Публикации обновлены через TanStack Query.",
      }),
    onError: (error) =>
      showToast({
        title: "Ошибка публикации",
        description: getRussianErrorMessage(error),
      }),
  });
  const variant = variantQuery.data;
  return (
    <main className="min-h-screen bg-slate-950 p-5 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="rounded-3xl border border-white/10 bg-white/[0.06] p-6">
          <Link href="/variants" className="text-sm text-cyan-200">
            ← К списку вариантов
          </Link>
          <div className="mt-4 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div>
              <p className="text-sm text-slate-400">Предпросмотр материала</p>
              <h1 className="mt-2 text-3xl font-bold text-white">
                {variant?.title || "Вариант загружается"}
              </h1>
              <p className="mt-2 text-slate-400">
                Статус: {statusText(variant?.status)}
              </p>
            </div>
            {variant &&
              (() => {
                const actionState = variantActionState(variant);
                return (
                  <div className="space-y-3 xl:max-w-xl">
                    <div className="flex flex-wrap gap-3">
                      <ActionButton
                        variant={actionState.isApproved ? "neutral" : "primary"}
                        disabled={
                          !actionState.canApprove ||
                          reject.isPending ||
                          exportVariant.isPending ||
                          publishTelegram.isPending
                        }
                        isLoading={approve.isPending}
                        loadingText="Одобряем…"
                        onClick={() => {
                          showToast({
                            title: "Выполняется…",
                            description:
                              "Отправляем вариант на одобрение и обновим данные страницы после ответа API.",
                            kind: "loading",
                          });
                          approve.mutate({ variantId });
                        }}
                      >
                        {actionState.isApproved ? "Уже одобрено" : "Одобрить"}
                      </ActionButton>
                      <ActionButton
                        variant="danger"
                        disabled={
                          variant.status === "rejected" ||
                          approve.isPending ||
                          exportVariant.isPending ||
                          publishTelegram.isPending
                        }
                        isLoading={reject.isPending}
                        loadingText="Отклоняем…"
                        onClick={() =>
                          reject.mutate({
                            variantId,
                            reason: "Отклонено из интерфейса",
                          })
                        }
                      >
                        {variant.status === "rejected"
                          ? "Уже отклонён"
                          : "Отклонить"}
                      </ActionButton>
                      <ActionButton
                        disabled={
                          !actionState.canPublish ||
                          approve.isPending ||
                          reject.isPending ||
                          publishTelegram.isPending
                        }
                        isLoading={exportVariant.isPending}
                        loadingText="Экспортируем…"
                        onClick={() => {
                          if (
                            !window.confirm(
                              "Экспортировать вариант в markdown? Будет создана запись публикации и файл экспорта для выбранной платформы; после ответа данные страницы обновятся.",
                            )
                          )
                            return;
                          showToast({
                            title: "Выполняется…",
                            description:
                              "Готовим экспорт публикации в markdown.",
                            kind: "loading",
                          });
                          exportVariant.mutate({
                            variantId,
                            platform: variant.platform as ExportPlatform,
                            export_format: "markdown",
                          });
                        }}
                      >
                        Экспортировать
                      </ActionButton>
                      <ActionButton
                        disabled={
                          !actionState.canPublish ||
                          approve.isPending ||
                          reject.isPending ||
                          exportVariant.isPending
                        }
                        isLoading={publishTelegram.isPending}
                        loadingText="Публикуем…"
                        onClick={() => {
                          if (
                            !window.confirm(
                              "Опубликовать вариант в Telegram? Одобренный текст будет отправлен в канал, а публикация получит статус и идентификатор сообщения после ответа API.",
                            )
                          )
                            return;
                          showToast({
                            title: "Выполняется…",
                            description: "Отправляем публикацию в Telegram.",
                            kind: "loading",
                          });
                          publishTelegram.mutate(variantId);
                        }}
                      >
                        Опубликовать в Telegram
                      </ActionButton>
                    </div>
                    <InlineNotice
                      tone={
                        actionState.canPublish
                          ? "success"
                          : actionState.isApproved
                            ? "success"
                            : "warning"
                      }
                    >
                      {actionState.approveReason}. Экспорт и публикация:{" "}
                      {actionState.publishReason}
                    </InlineNotice>
                  </div>
                );
              })()}
          </div>
          {(approve.isPending ||
            reject.isPending ||
            exportVariant.isPending ||
            publishTelegram.isPending) && (
            <div className="mt-4">
              <InlineNotice tone="info">
                Выполняется операция. Кнопка временно отключена, результат
                появится после ответа API.
              </InlineNotice>
            </div>
          )}
          {approve.isSuccess && (
            <div className="mt-4">
              <OperationResult
                title="Одобрение завершено"
                summary="Вариант переведён в статус одобренного; данные страницы обновлены."
              />
            </div>
          )}
          {exportVariant.isSuccess && (
            <div className="mt-4">
              <OperationResult
                title="Экспорт завершён"
                summary={`Создана запись публикации #${exportVariant.data.id}. Путь экспорта: ${exportVariant.data.export_path || "не указан"}. Данные обновлены.`}
              />
            </div>
          )}
          {publishTelegram.isSuccess && (
            <div className="mt-4">
              <OperationResult
                title="Публикация завершена"
                summary={`Создана публикация #${publishTelegram.data.id}. Message ID: ${publishTelegram.data.message_id || "не указан"}. Данные обновлены.`}
              />
            </div>
          )}
        </header>
        {variantQuery.isLoading && (
          <div className="rounded-3xl border border-white/10 bg-slate-900 p-5 text-slate-300">
            Загружаем материал…
          </div>
        )}
        {variantQuery.error && (
          <div className="rounded-3xl border border-rose-300/30 bg-rose-400/10 p-5 text-rose-100">
            Не удалось загрузить материал:{" "}
            {getRussianErrorMessage(variantQuery.error)}
          </div>
        )}
        {variant && (
          <div className="grid gap-5 xl:grid-cols-[1fr_24rem]">
            <div className="space-y-5">
              <Panel title="Предпросмотр">
                <article className="max-w-none">
                  <h2 className="text-2xl font-bold text-white">
                    {variant.title || "Без заголовка"}
                  </h2>
                  <p className="mt-4 text-xl text-cyan-100">
                    {variant.lead || "Лид не указан"}
                  </p>
                  <div className="mt-5 whitespace-pre-wrap text-slate-200">
                    {variant.body || "Текст body не указан"}
                  </div>
                </article>
              </Panel>
              <Panel title="Контент">
                <div className="whitespace-pre-wrap rounded-2xl border border-white/10 bg-slate-900/70 p-4 text-sm leading-7 text-slate-200">
                  {variant.content}
                </div>
              </Panel>
              <Panel title="Источники">
                <ul className="space-y-2">
                  {variant.sources?.length ? (
                    variant.sources.map((source) => (
                      <li
                        key={source}
                        className="rounded-2xl border border-white/10 bg-slate-900/60 p-3 text-sm text-cyan-100"
                      >
                        {source}
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-slate-400">
                      Источники не указаны.
                    </li>
                  )}
                </ul>
              </Panel>
            </div>
            <aside className="space-y-5">
              <Panel title="Панель метаданных">
                <MetadataPanel variant={variant} />
              </Panel>
              <Panel title="История статусов">
                <StatusTimeline variant={variant} />
              </Panel>
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}
