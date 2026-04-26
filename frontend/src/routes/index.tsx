import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ArrowRight, Search, ShoppingCart, UserCircle2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { loadSession, saveSession } from "@/lib/session";
import { useSnackbar } from "@/components/Snackbar";
import type { Question } from "@/lib/types";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Gazette — Ask anything. Discover everything." },
      { name: "description", content: "Tell Gazette what you need. Our AI concierge finds the perfect product across the web." },
      { property: "og:title", content: "Gazette — Ask anything. Discover everything." },
      { property: "og:description", content: "Agentic shopping concierge for the things you actually want." },
    ],
  }),
  component: Landing,
});

function Landing() {
  const navigate = useNavigate();
  const snack = useSnackbar();
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = value.trim();
    if (!q || loading) return;
    setLoading(true);
    try {
      const data = await api<{
        session_id: string;
        detected_category: string;
        initial_questions: Question[];
        mode: string;
        query: string;
      }>("/query", { method: "POST", body: JSON.stringify({ query: q }) });
      const prev = loadSession();
      saveSession({
        ...prev,
        session_id: data.session_id,
        query: q,
        detected_category: data.detected_category,
        current_questions: data.initial_questions,
        answers: {},
        answered_total: 0,
        total_estimate: Math.max(7, data.initial_questions.length + 4),
        mode: data.mode,
      });
      navigate({ to: "/questions" });
    } catch (err) {
      snack.show(err instanceof ApiError ? err.message : "Could not start your search", () => submit(e));
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ background: "var(--bg)" }}>
      {/* Top nav */}
      <header
        className="relative z-10 flex h-14 items-center justify-between px-6"
        style={{ background: "var(--surface)", borderBottom: "1px solid var(--outline-variant)" }}
      >
        <div className="font-display text-[22px] font-bold" style={{ color: "var(--primary)" }}>Gazette</div>
        <div className="flex items-center gap-5" style={{ color: "var(--on-surface-variant)" }}>
          <ShoppingCart size={22} />
          <UserCircle2 size={24} />
        </div>
      </header>

      {/* Ambient glow */}
      <div
        className="pointer-events-none absolute inset-0 -translate-y-32"
        style={{
          background:
            "radial-gradient(ellipse 55% 30% at 50% 57%, rgba(245,166,35,0.18) 0%, transparent 65%)",
        }}
      />

      {/* Center content */}
      <main className="relative z-10 flex min-h-[calc(100vh-56px)] flex-col items-center justify-center px-6 -translate-y-32">
        <h1
          className="font-display font-bold"
          style={{ color: "var(--primary)", fontSize: "72px", marginBottom: "32px", lineHeight: 1 }}
        >
          Gazette
        </h1>

        <form onSubmit={submit} className="w-full max-w-[620px]">
          <div
            className="flex h-[60px] items-center rounded-full px-2 pl-5"
            style={{
              background: "var(--surface-high)",
              border: "1px solid var(--outline-variant)",
              boxShadow: "0 0 0 1px rgba(245,166,35,0.35), 0 0 24px rgba(245,166,35,0.15)",
            }}
          >
            <Search size={20} style={{ color: "var(--outline)", marginRight: 12 }} />
            <input
              autoFocus
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="wireless earbuds for the gym..."
              className="flex-1 bg-transparent text-body-lg outline-none placeholder:text-[color:var(--outline)]"
              style={{ color: "var(--on-surface)" }}
            />
            <button
              type="submit"
              disabled={loading || !value.trim()}
              className="flex h-11 w-11 items-center justify-center rounded-full transition-all hover:scale-105"
              style={{
                background: "var(--primary-container)",
                transition: "all 150ms var(--ease-emphasized)",
                opacity: loading || !value.trim() ? 0.7 : 1,
              }}
              aria-label="Search"
            >
              <ArrowRight size={20} color="white" />
            </button>
          </div>
        </form>

        <div className="mt-4 text-body-md text-center" style={{ color: "var(--outline)" }}>
          Ask anything. Discover everything.
        </div>
      </main>
    </div>
  );
}
