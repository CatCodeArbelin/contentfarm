import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { QueryProvider } from "../components/query-provider";
import { ToastProvider } from "../components/toast-provider";

export const metadata: Metadata = {
  title: "Contentfarm — фронтенд",
  description: "Русскоязычный UI shell и базовая дизайн-система Contentfarm.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ru" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased">
        <ToastProvider>
          <QueryProvider>{children}</QueryProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
