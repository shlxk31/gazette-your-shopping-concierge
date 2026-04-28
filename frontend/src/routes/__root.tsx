import { Outlet, Link, createRootRoute, HeadContent, Scripts } from "@tanstack/react-router";
import appCss from "../styles.css?url";
import { SnackbarProvider } from "@/components/Snackbar";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4" style={{ background: "var(--bg)" }}>
      <div className="max-w-md text-center">
        <h1 className="font-display text-7xl font-bold" style={{ color: "var(--primary)" }}>404</h1>
        <h2 className="mt-4 text-title-lg" style={{ color: "var(--on-surface)" }}>Page not found</h2>
        <div className="mt-6">
          <Link to="/" className="inline-flex items-center justify-center rounded-full px-5 py-2.5 text-label-lg" style={{ background: "var(--primary-container)", color: "var(--on-primary)" }}>
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Gazette — Ask anything. Discover everything." },
      { name: "description", content: "Agentic shopping concierge that finds the perfect product for you." },
    ],
    links: [{ rel: "stylesheet", href: appCss }],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
});

function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <Scripts/>
      </>
  );
}

function RootComponent() {
  return (
    <SnackbarProvider>
      <Outlet />
    </SnackbarProvider>
  );
}
