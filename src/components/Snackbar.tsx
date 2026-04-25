import { createContext, useCallback, useContext, useEffect, useState } from "react";

type Snack = { id: number; message: string; onRetry?: () => void };
type Ctx = { show: (message: string, onRetry?: () => void) => void };

const SnackbarContext = createContext<Ctx>({ show: () => {} });

export function useSnackbar() {
  return useContext(SnackbarContext);
}

export function SnackbarProvider({ children }: { children: React.ReactNode }) {
  const [snacks, setSnacks] = useState<Snack[]>([]);
  const show = useCallback((message: string, onRetry?: () => void) => {
    const id = Date.now() + Math.random();
    setSnacks((s) => [...s, { id, message, onRetry }]);
  }, []);
  return (
    <SnackbarContext.Provider value={{ show }}>
      {children}
      <div className="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 flex-col gap-2">
        {snacks.map((s) => (
          <SnackItem key={s.id} snack={s} onClose={() => setSnacks((arr) => arr.filter((x) => x.id !== s.id))} />
        ))}
      </div>
    </SnackbarContext.Provider>
  );
}

function SnackItem({ snack, onClose }: { snack: Snack; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 6000);
    return () => clearTimeout(t);
  }, [onClose]);
  return (
    <div
      className="flex items-center gap-4 rounded-[var(--r-lg)] px-5 py-3.5 text-body-md"
      style={{ background: "var(--surface-high)", color: "var(--on-surface)" }}
    >
      <span>{snack.message}</span>
      {snack.onRetry && (
        <button
          onClick={() => {
            snack.onRetry?.();
            onClose();
          }}
          className="text-label-lg"
          style={{ color: "var(--primary)" }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
