import type { Question } from "./types";

const KEY = "gazette_session_v1";

export type SessionState = {
  session_id: string | null;
  query: string;
  detected_category: string | null;
  current_questions: Question[];
  answers: Record<string, any>;
  answered_total: number;
  total_estimate: number;
  mode: string | null;
};

const initial: SessionState = {
  session_id: null,
  query: "",
  detected_category: null,
  current_questions: [],
  answers: {},
  answered_total: 0,
  total_estimate: 7,
  mode: null,
};

export function loadSession(): SessionState {
  if (typeof window === "undefined") return initial;
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return initial;
    return { ...initial, ...JSON.parse(raw) };
  } catch {
    return initial;
  }
}

export function saveSession(s: SessionState) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(s));
}

export function clearSession() {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(KEY);
}
