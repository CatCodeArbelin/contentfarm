"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationOptions,
  type UseQueryOptions,
} from "@tanstack/react-query";

export type ApiStatus =
  | "draft"
  | "needs_review"
  | "pending"
  | "active"
  | "processing"
  | "pending_review"
  | "approved"
  | "rejected"
  | "scheduled"
  | "exported"
  | "published"
  | "failed"
  | "archived";

export type SortOrder = "asc" | "desc";
export type ExportFormat = "markdown" | "html";
export type ExportPlatform =
  | "telegram"
  | "dzen"
  | "max"
  | "vc"
  | "habr"
  | "dtf"
  | "pikabu";

export type PaginatedResponse<T> = {
  items: T[];
  limit: number;
  offset: number;
  total: number;
};

export type ListParams = {
  limit?: number;
  offset?: number;
  status?: ApiStatus;
  language?: string;
  topic?: string;
  platform?: string;
  strategy?: string;
  created_at?: string;
};

export type NewsEventListParams = ListParams & {
  min_score?: number;
  max_score?: number;
  sort_by?: "created_at" | "score";
  sort_order?: SortOrder;
};

export type HealthResponse = { status: string };

export type Source = {
  id: number;
  name: string;
  url: string;
  platform: string;
  language: string;
  topic: string | null;
  strategy: string | null;
  status: ApiStatus;
  created_at: string;
  updated_at: string | null;
};

export type SourceCreate = Omit<Source, "id" | "created_at" | "updated_at">;

export type RssCollectPayload = {
  source_id?: number;
  url?: string;
  name?: string;
  language?: string;
  topic?: string | null;
  strategy?: string | null;
};

export type RssCollectResponse = {
  source_id?: number;
  fetched?: number;
  created?: number;
  skipped?: number;
  [key: string]: number | undefined;
};

export type RawItem = {
  id: number;
  source_id: number;
  title: string;
  url: string;
  content: string;
  language: string;
  topic: string | null;
  platform: string | null;
  strategy: string | null;
  status: ApiStatus;
  created_at: string;
};

export type NewsEvent = {
  id: number;
  title: string;
  summary: string;
  language: string;
  topic: string | null;
  platform: string | null;
  strategy: string | null;
  status: ApiStatus;
  raw_item_ids: number[];
  score: number;
  risk_level: string | null;
  source_url: string | null;
  reasons: Record<string, unknown>[];
  created_at: string;
};

export type DeduplicateResponse = {
  processed?: number;
  created?: number;
  linked?: number;
  already_linked?: number;
  news_event_ids?: number[];
  source_link_ids?: number[];
  items?: Array<{
    news_event_id: number;
    source_link_id: number;
    created: boolean;
    already_linked: boolean;
  }>;
};

export type GenerateResponse = {
  generated_variants: Array<{
    id: number;
    news_event_id: number;
    title: string | null;
    lead: string | null;
    body: string | null;
    sources: string[] | null;
    platform: string;
    strategy: string;
    risk_level: string;
    status: ApiStatus;
    created_at: string;
  }>;
};

export type Variant = {
  id: number;
  generation_id: number;
  prompt_id: number | null;
  prompt_version: string | null;
  platform: string;
  strategy: string;
  language: string;
  topic: string | null;
  content: string;
  title: string | null;
  lead: string | null;
  body: string | null;
  sources: string[] | null;
  risk_level: string | null;
  score: number | null;
  status: ApiStatus;
  created_at: string;
  updated_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
};

export type Publication = {
  id: number;
  variant_id: number;
  platform: string;
  strategy: string;
  language: string | null;
  topic: string | null;
  status: ApiStatus;
  url: string | null;
  message_id: string | null;
  export_path: string | null;
  error: string | null;
  created_at: string;
  scheduled_at: string | null;
  published_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
};

type ApiErrorDetailItem = { msg?: string };

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export const apiErrorMessages = {
  missingBaseUrl: "Не задан адрес API. Укажите NEXT_PUBLIC_API_BASE_URL.",
  network:
    "Не удалось подключиться к серверу. Проверьте соединение и адрес API.",
  parse: "Сервер вернул некорректный ответ.",
  unknown: "Произошла неизвестная ошибка. Попробуйте ещё раз.",
} as const;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

function getApiBaseUrl() {
  if (!API_BASE_URL) {
    throw new ApiError(apiErrorMessages.missingBaseUrl);
  }
  return API_BASE_URL.replace(/\/$/, "");
}

function toQueryString(
  params?: Record<string, string | number | boolean | null | undefined>,
) {
  const searchParams = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function readError(response: Response) {
  try {
    const data = (await response.json()) as {
      detail?: string | ApiErrorDetailItem[];
    };
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail))
      return data.detail
        .map((item) => item?.msg)
        .filter(Boolean)
        .join("; ");
  } catch {
    return null;
  }
  return null;
}

function stripTechnicalDetails(message: string) {
  const firstLine =
    message.split(/\r?\n/)[0]?.trim() || apiErrorMessages.unknown;
  if (/traceback|stack trace|^error:/i.test(firstLine))
    return apiErrorMessages.unknown;
  return (
    firstLine.replace(/^Ошибка API:\s*/i, "").trim() || apiErrorMessages.unknown
  );
}

export function getRussianErrorMessage(error: unknown) {
  if (error instanceof ApiError) return stripTechnicalDetails(error.message);
  if (error instanceof Error && error.message)
    return stripTechnicalDetails(error.message);
  return apiErrorMessages.unknown;
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(apiErrorMessages.network, undefined, error);
  }

  if (!response.ok) {
    const backendMessage = await readError(response);
    throw new ApiError(
      backendMessage
        ? `Ошибка API: ${backendMessage}`
        : `Ошибка API: сервер вернул статус ${response.status}.`,
      response.status,
    );
  }

  if (response.status === 204) return undefined as T;

  try {
    return (await response.json()) as T;
  } catch (error) {
    throw new ApiError(apiErrorMessages.parse, response.status, error);
  }
}

export const api = {
  healthCheck: () => apiRequest<HealthResponse>("/health"),
  getSources: (params?: ListParams) =>
    apiRequest<PaginatedResponse<Source>>(
      `/api/v1/sources${toQueryString(params)}`,
    ),
  createSource: (payload: SourceCreate) =>
    apiRequest<Source>("/api/v1/sources", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  collectRss: (payload: RssCollectPayload) =>
    apiRequest<RssCollectResponse>("/api/v1/collectors/rss", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getRawItems: (params?: ListParams) =>
    apiRequest<PaginatedResponse<RawItem>>(
      `/api/v1/raw-items${toQueryString(params)}`,
    ),
  deduplicate: (limit = 100) =>
    apiRequest<DeduplicateResponse>(
      `/api/v1/news-events/deduplicate${toQueryString({ limit })}`,
      { method: "POST" },
    ),
  getNewsEvents: (params?: NewsEventListParams) =>
    apiRequest<PaginatedResponse<NewsEvent>>(
      `/api/v1/news-events${toQueryString(params)}`,
    ),
  generateNewsEvent: (newsEventId: number) =>
    apiRequest<GenerateResponse>(`/api/v1/generate/${newsEventId}`, {
      method: "POST",
    }),
  getVariants: (params?: ListParams) =>
    apiRequest<PaginatedResponse<Variant>>(
      `/api/v1/variants${toQueryString(params)}`,
    ),
  getVariant: (variantId: number) =>
    apiRequest<Variant>(`/api/v1/variants/${variantId}`),
  approveVariant: ({
    variantId,
    approved_by = "frontend",
  }: {
    variantId: number;
    approved_by?: string;
  }) =>
    apiRequest<Variant>(`/api/v1/variants/${variantId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved_by }),
    }),
  rejectVariant: ({
    variantId,
    reason,
    rejected_by = "frontend",
  }: {
    variantId: number;
    reason?: string | null;
    rejected_by?: string;
  }) =>
    apiRequest<Variant>(`/api/v1/variants/${variantId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason, rejected_by }),
    }),
  exportVariant: ({
    variantId,
    platform,
    export_format = "markdown",
  }: {
    variantId: number;
    platform: ExportPlatform;
    export_format?: ExportFormat;
  }) =>
    apiRequest<Publication>(`/api/v1/publications/${variantId}/export`, {
      method: "POST",
      body: JSON.stringify({ platform, format: export_format }),
    }),
  publishTelegram: (variantId: number) =>
    apiRequest<Publication>(
      `/api/v1/publications/${variantId}/publish-telegram`,
      { method: "POST" },
    ),
  getPublications: (params?: ListParams) =>
    apiRequest<PaginatedResponse<Publication>>(
      `/api/v1/publications${toQueryString(params)}`,
    ),
};

export const apiKeys = {
  health: ["health"] as const,
  sources: (params?: ListParams) => ["sources", params] as const,
  rawItems: (params?: ListParams) => ["raw-items", params] as const,
  newsEvents: (params?: NewsEventListParams) =>
    ["news-events", params] as const,
  variants: (params?: ListParams) => ["variants", params] as const,
  variant: (variantId: number) => ["variant", variantId] as const,
  publications: (params?: ListParams) => ["publications", params] as const,
};

type QueryConfig<T> = Omit<
  UseQueryOptions<T, ApiError>,
  "queryKey" | "queryFn"
>;
type MutationConfig<TData, TVariables> = UseMutationOptions<
  TData,
  ApiError,
  TVariables
>;

export function useHealthCheck(options?: QueryConfig<HealthResponse>) {
  return useQuery({
    queryKey: apiKeys.health,
    queryFn: api.healthCheck,
    ...options,
  });
}

export function useGetSources(
  params?: ListParams,
  options?: QueryConfig<PaginatedResponse<Source>>,
) {
  return useQuery({
    queryKey: apiKeys.sources(params),
    queryFn: () => api.getSources(params),
    ...options,
  });
}

export function useCreateSource(
  options?: MutationConfig<Source, SourceCreate>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: api.createSource,
    onSuccess: (...args) => {
      void queryClient.invalidateQueries({ queryKey: ["sources"] });
      options?.onSuccess?.(...args);
    },
  });
}

export function useCollectRss(
  options?: MutationConfig<RssCollectResponse, RssCollectPayload>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: api.collectRss,
    onSuccess: (...args) => {
      void queryClient.invalidateQueries({ queryKey: ["sources"] });
      void queryClient.invalidateQueries({ queryKey: ["raw-items"] });
      options?.onSuccess?.(...args);
    },
  });
}

export function useGetRawItems(
  params?: ListParams,
  options?: QueryConfig<PaginatedResponse<RawItem>>,
) {
  return useQuery({
    queryKey: apiKeys.rawItems(params),
    queryFn: () => api.getRawItems(params),
    ...options,
  });
}

export function useDeduplicate(
  options?: MutationConfig<DeduplicateResponse, number | undefined>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: api.deduplicate,
    onSuccess: (...args) => {
      void queryClient.invalidateQueries({ queryKey: ["news-events"] });
      void queryClient.invalidateQueries({ queryKey: ["raw-items"] });
      options?.onSuccess?.(...args);
    },
  });
}

export function useGetNewsEvents(
  params?: NewsEventListParams,
  options?: QueryConfig<PaginatedResponse<NewsEvent>>,
) {
  return useQuery({
    queryKey: apiKeys.newsEvents(params),
    queryFn: () => api.getNewsEvents(params),
    ...options,
  });
}

export function useGenerateNewsEvent(
  options?: MutationConfig<GenerateResponse, number>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: api.generateNewsEvent,
    onSuccess: (...args) => {
      void queryClient.invalidateQueries({ queryKey: ["variants"] });
      void queryClient.invalidateQueries({ queryKey: ["news-events"] });
      options?.onSuccess?.(...args);
    },
  });
}

export function useGetVariants(
  params?: ListParams,
  options?: QueryConfig<PaginatedResponse<Variant>>,
) {
  return useQuery({
    queryKey: apiKeys.variants(params),
    queryFn: () => api.getVariants(params),
    ...options,
  });
}

export function useGetVariant(
  variantId: number,
  options?: QueryConfig<Variant>,
) {
  return useQuery({
    queryKey: apiKeys.variant(variantId),
    queryFn: () => api.getVariant(variantId),
    enabled: variantId > 0,
    ...options,
  });
}

export function useApproveVariant(
  options?: MutationConfig<
    Variant,
    { variantId: number; approved_by?: string }
  >,
) {
  const queryClient = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: api.approveVariant,
    onSuccess: (data, ...args) => {
      void queryClient.invalidateQueries({ queryKey: ["variants"] });
      void queryClient.invalidateQueries({
        queryKey: apiKeys.variant(data.id),
      });
      options?.onSuccess?.(data, ...args);
    },
  });
}

export function useRejectVariant(
  options?: MutationConfig<
    Variant,
    { variantId: number; reason?: string | null; rejected_by?: string }
  >,
) {
  const queryClient = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: api.rejectVariant,
    onSuccess: (data, ...args) => {
      void queryClient.invalidateQueries({ queryKey: ["variants"] });
      void queryClient.invalidateQueries({
        queryKey: apiKeys.variant(data.id),
      });
      options?.onSuccess?.(data, ...args);
    },
  });
}

export function useExportVariant(
  options?: MutationConfig<
    Publication,
    {
      variantId: number;
      platform: ExportPlatform;
      export_format?: ExportFormat;
    }
  >,
) {
  const queryClient = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: api.exportVariant,
    onSuccess: (...args) => {
      void queryClient.invalidateQueries({ queryKey: ["publications"] });
      void queryClient.invalidateQueries({ queryKey: ["variants"] });
      void queryClient.invalidateQueries({
        queryKey: apiKeys.variant(args[1].variantId),
      });
      options?.onSuccess?.(...args);
    },
  });
}

export function usePublishTelegram(
  options?: MutationConfig<Publication, number>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    ...options,
    mutationFn: api.publishTelegram,
    onSuccess: (...args) => {
      void queryClient.invalidateQueries({ queryKey: ["publications"] });
      void queryClient.invalidateQueries({ queryKey: ["variants"] });
      void queryClient.invalidateQueries({
        queryKey: apiKeys.variant(args[1]),
      });
      options?.onSuccess?.(...args);
    },
  });
}

export function useGetPublications(
  params?: ListParams,
  options?: QueryConfig<PaginatedResponse<Publication>>,
) {
  return useQuery({
    queryKey: apiKeys.publications(params),
    queryFn: () => api.getPublications(params),
    ...options,
  });
}
