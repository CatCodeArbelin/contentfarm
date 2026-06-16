import type { ApiStatus } from "./api";

export const statusLabels: Partial<Record<ApiStatus | string, string>> = {
  draft: "Черновик",
  needs_review: "Нужна проверка",
  pending: "Ожидает",
  active: "Активен",
  processing: "В работе",
  pending_review: "На модерации",
  approved: "Одобрен",
  rejected: "Отклонён",
  scheduled: "Запланирована",
  exported: "Экспортирована",
  published: "Опубликована",
  failed: "Ошибка",
  archived: "Архив",
  skipped: "Пропущено",
  collected: "Собрано",
  healthy: "Работает",
  ok: "Работает",
};

export function statusText(status?: ApiStatus | string | null) {
  if (!status) return "Неизвестно";
  return statusLabels[status] ?? status;
}

export function technicalValue(value?: string | number | null) {
  if (value === null || value === undefined || String(value).trim() === "") return "—";
  return String(value);
}

export function riskLevelText(riskLevel?: string | null) {
  const labels: Record<string, string> = {
    low: "Низкий",
    medium: "Средний",
    high: "Высокий",
  };
  return labels[riskLevel ?? ""] ?? (riskLevel || "Не указан");
}
