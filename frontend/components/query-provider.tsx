"use client";

import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { getRussianErrorMessage } from "../src/lib/api";
import { useToast } from "./toast-provider";

export function QueryProvider({ children }: { children: ReactNode }) {
  const { showToast } = useToast();
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onError: (error) => {
            showToast({ title: "Ошибка загрузки", description: getRussianErrorMessage(error) });
          },
        }),
        mutationCache: new MutationCache({
          onError: (error) => {
            showToast({ title: "Ошибка действия", description: getRussianErrorMessage(error) });
          },
        }),
        defaultOptions: {
          queries: {
            retry: 1,
            throwOnError: false,
          },
          mutations: {
            throwOnError: false,
          },
        },
      }),
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
