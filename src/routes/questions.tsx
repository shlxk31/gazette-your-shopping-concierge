import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { api, ApiError } from "@/lib/api";
import { loadSession, saveSession } from "@/lib/session";
import { useSnackbar } from "@/components/Snackbar";
import type { Question } from "@/lib/types";
import { ArrowRight, Check, ChevronDown, MessageSquare, Wallet, Code2, SlidersHorizontal, Tag } from "lucide-react";

export const Route = createFileRoute("/questions")({
  head: () => ({
    meta: [
      { title: "Refine your search — Gazette" },
      { name: "description", content: "Answer a few quick questions so the Gazette concierge can find your perfect match." },
    ],
  }),
  component: QuestionsPage,
});

function categoryIcon(cat: string) {
  if (cat === "budget") return Wallet;
  if (cat === "usage") return Code2;
  if (cat === "preference" || cat === "technical") return SlidersHorizontal;
  if (cat === "brand") return Tag;
  return SlidersHorizontal;
}

function dependencyMet(q: Question, answers: Record<string, any>) {
  if (!q.depends_on) return true;
  const v = answers[q.depends_on.question_id];
  if (Array.isArray(v)) return v.includes(q.depends_on.value);
  return v === q.depends_on.value;
}

function QuestionsPage() {
  const navigate = useNavigate();
  const snack = useSnackbar();
  const [session, setSession] = useState(() => loadSession());
  const [submitting, setSubmitting] = useState(false);
  const [chatMsg, setChatMsg] = useState("");
  const [batch, setBatch] = useState(1);

  useEffect(() => {
    if (!session.session_id) {
      navigate({ to: "/" });
    }
  }, [session.session_id, navigate]);

  const setAnswer = (qid: string, value: any) => {
    const next = { ...session, answers: { ...session.answers, [qid]: value } };
    const answeredCount = Object.keys(next.answers).filter((k) => {
      const v = next.answers[k];
      return v !== undefined && v !== null && !(Array.isArray(v) && v.length === 0) && v !== "";
    }).length;
    next.answered_total = answeredCount;
    setSession(next);
    saveSession(next);
  };

  const visibleQuestions = useMemo(
    () => session.current_questions.filter((q) => dependencyMet(q, session.answers)),
    [session.current_questions, session.answers]
  );

  const allRequiredAnswered = visibleQuestions
    .filter((q) => q.is_required)
    .every((q) => {
      const v = session.answers[q.id];
      if (q.input_type === "range_slider") return v !== undefined && v !== null;
      if (q.input_type === "checkbox") return Array.isArray(v) && v.length > 0;
      return v !== undefined && v !== null && v !== "";
    });

  const onContinue = async () => {
    if (submitting || !session.session_id) return;
    setSubmitting(true);
    try {
      const answers = Object.entries(session.answers).map(([question_id, value]) => ({ question_id, value }));
      const data = await api<{
        next_questions: Question[] | null;
        is_complete: boolean;
        redirect_to: string | null;
      }>("/api/questions/answer", {
        method: "POST",
        body: JSON.stringify({
          session_id: session.session_id,
          answers,
          category: session.detected_category,
          batch,
        }),
      });
      if (data.is_complete) {
        navigate({ to: "/results" });
        return;
      }
      const nextQ = data.next_questions || [];
      const next = {
        ...session,
        current_questions: nextQ,
        answers: { ...session.answers },
      };
      setSession(next);
      saveSession(next);
      setBatch((b) => b + 1);
    } catch (err) {
      snack.show(err instanceof ApiError ? err.message : "Could not save your answers", onContinue);
    } finally {
      setSubmitting(false);
    }
  };

  const sendChat = async () => {
    const m = chatMsg.trim();
    if (!m || !session.session_id) return;
    setChatMsg("");
    try {
      const data = await api<{ message: string; updated_questions: Question[] | null }>("/api/chat", {
        method: "POST",
        body: JSON.stringify({ session_id: session.session_id, message: m }),
      });
      snack.show(data.message);
      if (data.updated_questions && data.updated_questions.length) {
        const next = { ...session, current_questions: [...session.current_questions, ...data.updated_questions] };
        setSession(next);
        saveSession(next);
      }
    } catch (err) {
      snack.show(err instanceof ApiError ? err.message : "Message failed");
    }
  };

  return (
    <div style={{ background: "var(--bg)", minHeight: "100vh" }}>
      <Sidebar variant="questions" />
      <main className="ml-[268px] px-16 py-12 pb-32">
        <div className="mx-auto max-w-[820px]">
          <h1 className="font-display text-[32px] font-bold leading-tight" style={{ color: "var(--on-surface)" }}>
            Let's refine your search.
          </h1>
          <p className="mt-2 text-body-lg" style={{ color: "var(--on-surface-variant)" }}>
            Answer a few questions so our concierge can find the perfect match.
          </p>

          <div className="mt-10 flex flex-col gap-4">
            {session.current_questions.map((q, i) => {
              const visible = dependencyMet(q, session.answers);
              return (
                <div
                  key={q.id}
                  style={{
                    maxHeight: visible ? 1000 : 0,
                    opacity: visible ? 1 : 0,
                    overflow: "hidden",
                    transition:
                      "max-height 300ms var(--ease-emphasized), opacity 200ms 100ms var(--ease-emphasized)",
                  }}
                >
                  <div
                    className="card-in rounded-[var(--r-xl)] p-7"
                    style={{
                      background: "var(--surface-container)",
                      border: "1px solid var(--outline-variant)",
                      animationDelay: `${i * 60}ms`,
                    }}
                  >
                    <QuestionHeader q={q} />
                    <div className="mt-6">
                      <QuestionInput q={q} value={session.answers[q.id]} onChange={(v) => setAnswer(q.id, v)} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-8 flex justify-end">
            <button
              onClick={onContinue}
              disabled={!allRequiredAnswered || submitting}
              className="flex h-12 items-center gap-2 rounded-full px-8 text-label-lg transition-all"
              style={{
                background: allRequiredAnswered ? "var(--primary-container)" : "var(--surface-high)",
                color: allRequiredAnswered ? "var(--on-primary)" : "var(--outline)",
                opacity: submitting ? 0.7 : 1,
              }}
            >
              Continue <ArrowRight size={18} />
            </button>
          </div>
        </div>

        <div
          className="fixed bottom-0 left-[268px] right-0 px-16 pb-6 pt-4"
          style={{
            background:
              "linear-gradient(to top, var(--bg) 60%, color-mix(in oklab, var(--bg) 80%, transparent) 100%)",
          }}
        >
          <div className="mx-auto max-w-[820px]">
            <div
              className="flex items-center gap-3 rounded-full py-3 pl-5 pr-3"
              style={{
                background: "var(--surface-container)",
                border: "1px solid var(--outline-variant)",
              }}
            >
              <MessageSquare size={18} style={{ color: "var(--outline)" }} />
              <input
                value={chatMsg}
                onChange={(e) => setChatMsg(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") sendChat();
                }}
                placeholder="Type a specific requirement..."
                className="flex-1 bg-transparent text-body-md outline-none placeholder:text-[color:var(--outline)]"
                style={{ color: "var(--on-surface)" }}
              />
              <button
                onClick={sendChat}
                className="flex h-11 w-11 items-center justify-center rounded-full"
                style={{ background: "var(--primary-container)" }}
                aria-label="Send"
              >
                <ArrowRight size={18} color="white" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function QuestionHeader({ q }: { q: Question }) {
  const Icon = categoryIcon(q.category);
  return (
    <div className="flex items-center gap-4">
      <div
        className="flex h-9 w-9 items-center justify-center rounded-[var(--r-md)]"
        style={{ background: "var(--surface-high)" }}
      >
        <Icon size={18} style={{ color: "var(--primary)" }} />
      </div>
      <h2 className="text-title-lg" style={{ color: "var(--on-surface)" }}>
        {q.question_text}
      </h2>
    </div>
  );
}

function QuestionInput({
  q,
  value,
  onChange,
}: {
  q: Question;
  value: any;
  onChange: (v: any) => void;
}) {
  if (q.input_type === "range_slider" && q.range) {
    const cur = typeof value === "number" ? value : q.default_value ?? q.range.min;
    const pct = ((cur - q.range.min) / (q.range.max - q.range.min)) * 100;
    const symbol = q.range.unit === "INR" ? "₹" : q.range.unit === "USD" ? "$" : "";
    const fmt = (n: number) =>
      q.range!.unit === "INR" ? symbol + n.toLocaleString("en-IN") : symbol + n.toLocaleString();

    if (value === undefined || value === null) {
      queueMicrotask(() => onChange(cur));
    }

    return (
      <div className="px-2 pt-8 pb-2">
        <div className="relative h-6">
          <div
            className="absolute -top-2 -translate-x-1/2 rounded-full font-mono text-label-lg"
            style={{
              left: `${pct}%`,
              background: "var(--primary)",
              color: "var(--on-primary)",
              padding: "6px 14px",
              boxShadow: "0 0 12px rgba(245,166,35,0.4)",
            }}
          >
            {fmt(cur)}
          </div>
        </div>
        <input
          type="range"
          className="gz-slider mt-6"
          min={q.range.min}
          max={q.range.max}
          step={q.range.step}
          value={cur}
          onChange={(e) => onChange(Number(e.target.value))}
          style={
            {
              ["--track-bg" as any]: `linear-gradient(to right, var(--primary) 0% ${pct}%, var(--surface-highest) ${pct}% 100%)`,
            } as React.CSSProperties
          }
        />
        <div className="mt-3 flex justify-between font-mono" style={{ color: "var(--outline)", fontSize: 13 }}>
          <span>{fmt(q.range.min)}</span>
          <span>{fmt(q.range.max)}</span>
        </div>
      </div>
    );
  }

  if (q.input_type === "checkbox" && q.options) {
    const arr: string[] = Array.isArray(value) ? value : [];
    const toggle = (v: string) => {
      onChange(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);
    };
    return (
      <div className="flex flex-wrap gap-2">
        {q.options.map((opt) => {
          const active = arr.includes(opt.value);
          return (
            <button
              key={opt.value}
              onClick={() => toggle(opt.value)}
              className="flex items-center gap-2 rounded-full px-5 py-2.5 text-label-lg transition-colors"
              style={
                active
                  ? { background: "var(--primary-container)", color: "var(--on-primary)" }
                  : {
                      background: "var(--surface-high)",
                      color: "var(--on-surface-variant)",
                      border: "1px solid var(--outline-variant)",
                    }
              }
            >
              {active && <Check size={14} />}
              {opt.label}
            </button>
          );
        })}
      </div>
    );
  }

  if (q.input_type === "radio" && q.options) {
    return (
      <div className="flex flex-wrap gap-2">
        {q.options.map((opt) => {
          const active = value === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => onChange(opt.value)}
              className="rounded-full px-5 py-2.5 text-label-lg transition-colors"
              style={
                active
                  ? { background: "var(--primary-container)", color: "var(--on-primary)" }
                  : {
                      background: "var(--surface-high)",
                      color: "var(--on-surface-variant)",
                      border: "1px solid var(--outline-variant)",
                    }
              }
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    );
  }

  if (q.input_type === "dropdown" && q.options) {
    return <Dropdown q={q} value={value} onChange={onChange} />;
  }

  if (q.input_type === "text_input") {
    return (
      <input
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={q.placeholder || ""}
        className="w-full rounded-[var(--r-md)] px-4 py-3.5 text-body-lg outline-none transition-all focus:border-2"
        style={{
          background: "var(--surface-container)",
          border: "1px solid var(--outline)",
          color: "var(--on-surface)",
        }}
      />
    );
  }

  return null;
}

function Dropdown({ q, value, onChange }: { q: Question; value: any; onChange: (v: any) => void }) {
  const [open, setOpen] = useState(false);
  const sel = q.options?.find((o) => o.value === value);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between rounded-[var(--r-md)] px-4 py-3.5 text-label-lg"
        style={{
          background: "var(--surface-container)",
          border: "1px solid var(--outline)",
          color: "var(--on-surface)",
        }}
      >
        <span>{sel?.label || q.placeholder || "Select..."}</span>
        <ChevronDown size={18} style={{ color: "var(--outline)" }} />
      </button>
      {open && (
        <div
          className="absolute left-0 right-0 top-full z-20 mt-2 overflow-hidden rounded-[var(--r-lg)]"
          style={{ background: "var(--surface-high)", border: "1px solid var(--outline-variant)" }}
        >
          {q.options?.map((opt) => (
            <button
              key={opt.value}
              onClick={() => {
                onChange(opt.value);
                setOpen(false);
              }}
              className="flex h-11 w-full items-center px-4 text-left text-label-lg transition-colors hover:bg-[color:var(--surface-highest)]"
              style={{
                background: opt.value === value ? "var(--surface-highest)" : "transparent",
                color: "var(--on-surface)",
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
