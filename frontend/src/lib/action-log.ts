"use client";

export type ActionLogTone = "success" | "warning" | "error" | "info";

export type ActionLogEntry = {
  id: string;
  timestamp: string;
  action: string;
  result: string;
  href?: string;
  linkLabel?: string;
  tone?: ActionLogTone;
};

const STORAGE_KEY = "contentfarm.actionLog.v1";
const EVENT_NAME = "contentfarm-action-log-updated";
const MAX_ENTRIES = 30;

function canUseStorage() {
  return typeof window !== "undefined" && Boolean(window.sessionStorage);
}

function readEntries(): ActionLogEntry[] {
  if (!canUseStorage()) return [];
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ActionLogEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeEntries(entries: ActionLogEntry[]) {
  if (!canUseStorage()) return;
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_ENTRIES)));
  window.dispatchEvent(new Event(EVENT_NAME));
}

export function getActionLogEntries() {
  return readEntries();
}

export function addActionLogEntry(entry: Omit<ActionLogEntry, "id" | "timestamp">) {
  const nextEntry: ActionLogEntry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    timestamp: new Date().toISOString(),
    ...entry,
  };
  writeEntries([nextEntry, ...readEntries()]);
  return nextEntry;
}

export function subscribeActionLog(listener: () => void) {
  if (typeof window === "undefined") return () => undefined;
  window.addEventListener(EVENT_NAME, listener);
  window.addEventListener("storage", listener);
  return () => {
    window.removeEventListener(EVENT_NAME, listener);
    window.removeEventListener("storage", listener);
  };
}
