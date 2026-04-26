import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { Search, Home, Grid2x2, Box, Settings, HelpCircle, Shield } from "lucide-react";
import { clearSession, loadSession } from "@/lib/session";

type Props = {
  variant: "questions" | "results";
};

export function Sidebar({ variant }: Props) {
  const navigate = useNavigate();
  const session = typeof window !== "undefined" ? loadSession() : null;
  const router = useRouterState();
  const path = router.location.pathname;

  const onNewSearch = () => {
    clearSession();
    navigate({ to: "/" });
  };

  const navItems = [
    { to: "/", label: "Home", icon: Home, key: "home" },
    { to: "/questions", label: "Current Search", icon: Search, key: "questions" },
    { to: "/results", label: "Collections", icon: Grid2x2, key: "results" },
    { to: "/results", label: "Orders", icon: Box, key: "orders" },
    { to: "/results", label: "Settings", icon: Settings, key: "settings" },
  ];

  const activeKey = path === "/questions" ? "questions" : path === "/results" ? "results" : "home";
  const progress = session
    ? Math.min(100, Math.round((session.answered_total / Math.max(1, session.total_estimate)) * 100))
    : 0;

  return (
    <aside
      className="fixed left-0 top-0 flex h-screen w-[268px] flex-col px-5 py-6"
      style={{ background: "var(--surface)" }}
    >
      <div className="px-2 text-2xl font-display font-bold" style={{ color: "var(--primary)" }}>
        Gazette
      </div>

      {/* Concierge card */}
      <div
        className="mt-6 rounded-[var(--r-lg)] p-4"
        style={{ background: "var(--surface-container)" }}
      >
        <div className="flex items-start gap-3">
          {variant === "results" ? (
            <div
              className="h-9 w-9 shrink-0 rounded-full"
              style={{
                background:
                  "linear-gradient(135deg, var(--primary-container), var(--primary-dim))",
              }}
            />
          ) : (
            <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ background: "var(--primary)" }} />
          )}
          <div className="min-w-0">
            <div className="text-label-lg" style={{ color: "var(--on-surface)" }}>
              Gazette Concierge
            </div>
            <div className="text-label-sm" style={{ color: "var(--on-surface-variant)" }}>
              Agent: Active • {progress || 85}% Task Progress
            </div>
          </div>
        </div>
      </div>

      {/* Current Query (questions only) */}
      {variant === "questions" && session?.query && (
        <div
          className="mt-3 rounded-[var(--r-lg)] p-4"
          style={{ background: "var(--surface-container)" }}
        >
          <div
            className="text-label-sm uppercase tracking-wider font-mono"
            style={{ color: "var(--outline)" }}
          >
            CURRENT QUERY
          </div>
          <div
            className="mt-2 italic text-body-md"
            style={{ color: "var(--on-surface-variant)" }}
          >
            "{session.query}"
          </div>
        </div>
      )}

      {/* New search button */}
      <button
        onClick={onNewSearch}
        className="mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-full text-label-lg transition-all"
        style={
          variant === "results"
            ? {
                background: "var(--primary-container)",
                color: "var(--on-primary)",
              }
            : {
                border: "1px solid var(--outline-variant)",
                color: "var(--on-surface)",
              }
        }
      >
        <Search size={16} />
        New Search
      </button>

      {/* Progress (questions only) */}
      {variant === "questions" && session && (
        <div className="mt-5 px-1">
          <div className="flex items-center justify-between">
            <div className="text-label-sm" style={{ color: "var(--outline)" }}>
              Questionnaire Progress
            </div>
            <div className="text-label-md" style={{ color: "var(--primary)" }}>
              {session.answered_total} of {session.total_estimate} answered
            </div>
          </div>
          <div
            className="mt-2 h-1 w-full overflow-hidden rounded-full"
            style={{ background: "var(--surface-highest)" }}
          >
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${progress}%`, background: "var(--primary)" }}
            />
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className="mt-8 flex flex-col gap-1">
        {navItems.map((item) => {
          const active = activeKey === item.key;
          return (
            <Link
              key={item.label}
              to={item.to}
              className="flex h-12 items-center gap-3 rounded-full px-4 text-label-lg transition-colors"
              style={
                active
                  ? { background: "var(--primary-container)", color: "var(--on-primary)" }
                  : { color: "var(--on-surface-variant)" }
              }
            >
              <item.icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-1">
        <div className="flex h-10 items-center gap-3 px-4 text-label-md" style={{ color: "var(--on-surface-variant)" }}>
          <HelpCircle size={16} /> Help
        </div>
        <div className="flex h-10 items-center gap-3 px-4 text-label-md" style={{ color: "var(--on-surface-variant)" }}>
          <Shield size={16} /> Privacy
        </div>
      </div>
    </aside>
  );
}
