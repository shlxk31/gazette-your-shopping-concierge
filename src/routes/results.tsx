import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { api, ApiError } from "@/lib/api";
import { loadSession } from "@/lib/session";
import { useSnackbar } from "@/components/Snackbar";
import type { Price, Product } from "@/lib/types";
import { Search, ThumbsUp, ThumbsDown, ExternalLink, MessageCircle, Youtube } from "lucide-react";
import { currencySymbol } from "@/lib/format";

export const Route = createFileRoute("/results")({
  head: () => ({
    meta: [
      { title: "Curated Results — Gazette" },
      { name: "description", content: "Top picks from across the web, curated by your Gazette concierge." },
    ],
  }),
  component: ResultsPage,
});

function ResultsPage() {
  const navigate = useNavigate();
  const snack = useSnackbar();
  const session = loadSession();
  const [products, setProducts] = useState<Product[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session.session_id) {
      navigate({ to: "/" });
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await api<{ products: Product[] }>(
          `/api/products?session_id=${session.session_id}&category=${session.detected_category || "general"}`
        );
        if (!cancelled) {
          setProducts(data.products.slice(0, 5));
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          snack.show(err instanceof ApiError ? err.message : "Could not load products");
          setProducts([]);
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const topPickId =
    products && products.length
      ? products.reduce((a, b) => (b.match_score > a.match_score ? b : a)).id
      : null;

  return (
    <div style={{ background: "var(--bg)", minHeight: "100vh" }}>
      <Sidebar variant="results" />
      <main className="ml-[268px] px-16 py-12">
        <div className="flex items-center gap-2 text-body-md" style={{ color: "var(--outline)" }}>
          <Search size={14} />
          <span>"{session.query || "your search"}"</span>
        </div>
        <h1 className="mt-1 font-display text-[36px] font-bold" style={{ color: "var(--on-surface)" }}>
          Curated Results
        </h1>
        <p className="mt-2 mb-8 text-body-md" style={{ color: "var(--on-surface-variant)" }}>
          We've analyzed 450+ reviews across Reddit, YouTube, and specialized {session.detected_category?.replace(/_/g, " ") || "expert"} blogs to find these top recommendations.
        </p>

        {loading && <ProductGridSkeleton />}

        {!loading && products && products.length === 0 && <EmptyState />}

        {!loading && products && products.length > 0 && (
          <div className="grid gap-5" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))" }}>
            {products.map((p, i) => (
              <ProductCard key={p.id} product={p} isTopPick={p.id === topPickId} index={i} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function ProductGridSkeleton() {
  return (
    <div className="grid gap-5" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))" }}>
      {[0, 1].map((i) => (
        <div
          key={i}
          className="overflow-hidden rounded-[var(--r-xl)]"
          style={{ background: "var(--surface-container)", border: "1px solid var(--outline-variant)" }}
        >
          <div className="shimmer h-56 w-full" />
          <div className="space-y-3 p-5">
            <div className="shimmer h-6 w-3/4 rounded" />
            <div className="shimmer h-4 w-1/2 rounded" />
            <div className="shimmer h-20 w-full rounded" />
            <div className="shimmer h-12 w-full rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <Search size={48} style={{ color: "var(--outline)" }} />
      <h2 className="mt-6 text-title-lg" style={{ color: "var(--on-surface)" }}>
        Nothing matched perfectly
      </h2>
      <p className="mt-2 text-body-md" style={{ color: "var(--on-surface-variant)" }}>
        Try broadening your search or adjusting your budget.
      </p>
      <button
        onClick={() => navigate({ to: "/" })}
        className="mt-6 rounded-full px-6 py-2.5 text-label-lg"
        style={{ border: "1px solid var(--outline-variant)", color: "var(--on-surface)" }}
      >
        ← Start over
      </button>
    </div>
  );
}

function ProductCard({ product, isTopPick, index }: { product: Product; isTopPick: boolean; index: number }) {
  const [prices, setPrices] = useState<Price[] | null>(null);
  const [pricesLoading, setPricesLoading] = useState(true);
  const [showCompare, setShowCompare] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api<{ prices: Price[] }>(`/api/products/${product.id}/prices`);
        if (!cancelled) {
          setPrices(data.prices);
          setPricesLoading(false);
        }
      } catch {
        if (!cancelled) {
          setPrices([]);
          setPricesLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [product.id]);

  const best = prices?.find((p) => p.is_best) || prices?.[0];
  const highlight = product.review_summary?.highlights?.[0];
  const isReddit = highlight?.toLowerCase().includes("reddit") || highlight?.toLowerCase().includes("r/");
  const isYoutube = highlight?.toLowerCase().includes("youtube") || highlight?.toLowerCase().includes("youtuber");

  return (
    <div
      className="card-in relative flex flex-col overflow-hidden rounded-[var(--r-xl)]"
      style={{
        background: "var(--surface-container)",
        border: "1px solid var(--outline-variant)",
        animationDelay: `${index * 80}ms`,
      }}
    >
      {/* Image */}
      <div className="relative" style={{ background: "var(--surface-high)", aspectRatio: "16/9" }}>
        {product.image ? (
          <img src={product.image} alt={product.name} className="h-full w-full object-cover" loading="lazy" />
        ) : (
          <div className="flex h-full items-center justify-center" style={{ color: "var(--outline)" }}>
            <Search size={42} />
          </div>
        )}
        <div
          className="pointer-events-none absolute inset-x-0 bottom-0 h-1/3"
          style={{ background: "linear-gradient(transparent, var(--surface-container))" }}
        />
        {isTopPick && (
          <div
            className="absolute left-0 top-0 flex items-center gap-1.5 px-3.5 py-1.5"
            style={{
              background: "var(--surface-high)",
              borderRadius: "0 0 var(--r-md) 0",
            }}
          >
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--primary-dim)" }} />
            <span className="text-label-md" style={{ color: "var(--on-surface)" }}>
              TOP PICK
            </span>
          </div>
        )}
      </div>

      {/* Name + score */}
      <div className="relative px-5 pb-0 pt-4">
        <div className="flex items-start justify-between gap-4">
          <h3 className="text-title-lg font-medium" style={{ color: "var(--on-surface)" }}>
            {product.name}
          </h3>
          <div
            className="flex h-[60px] w-[60px] shrink-0 -translate-y-10 flex-col items-center justify-center rounded-full"
            style={{
              background: "var(--surface-high)",
              border: "2px solid var(--primary-container)",
            }}
          >
            <span className="font-display text-xl font-bold leading-none" style={{ color: "var(--on-surface)" }}>
              {product.match_score}
            </span>
            <span className="mt-0.5 text-label-sm" style={{ color: "var(--outline)" }}>
              % FIT
            </span>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col gap-4 px-5 pb-5">
        {highlight && (
          <div className="flex items-center gap-2 text-label-md" style={{ color: "var(--on-surface-variant)" }}>
            {isReddit ? <MessageCircle size={14} /> : isYoutube ? <Youtube size={14} /> : <MessageCircle size={14} />}
            <span>{highlight}</span>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {product.features.slice(0, 4).map((f) => (
            <span
              key={f}
              className="rounded-full px-3.5 py-1.5 text-label-md"
              style={{
                background: "var(--surface-high)",
                border: "1px solid var(--outline-variant)",
                color: "var(--on-surface-variant)",
              }}
            >
              {f}
            </span>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-5">
          <div>
            <div className="flex items-center gap-2 text-label-lg" style={{ color: "var(--on-surface)" }}>
              <ThumbsUp size={16} style={{ color: "var(--primary)" }} />
              Why we picked this
            </div>
            <ul className="mt-3 space-y-2">
              {product.match_reasons.slice(0, 3).map((r) => (
                <li key={r} className="flex gap-2 text-body-md" style={{ color: "var(--on-surface-variant)" }}>
                  <span style={{ color: "var(--primary)" }}>•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
          {product.missing_features && product.missing_features.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-label-lg" style={{ color: "var(--on-surface)" }}>
                <ThumbsDown size={16} style={{ color: "var(--outline)" }} />
                What it's missing
              </div>
              <ul className="mt-3 space-y-2">
                {product.missing_features.slice(0, 2).map((m) => (
                  <li key={m} className="flex gap-2 text-body-md" style={{ color: "var(--on-surface-variant)" }}>
                    <span style={{ color: "var(--outline)" }}>•</span>
                    <span>{m}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Price footer */}
      <div
        className="flex flex-col gap-3 px-5 py-4"
        style={{ background: "var(--surface-high)", borderTop: "1px solid var(--outline-variant)" }}
      >
        <div className="flex items-center justify-between">
          <span className="text-label-sm uppercase tracking-wider" style={{ color: "var(--outline)" }}>
            Best Price Found
          </span>
          {pricesLoading ? (
            <div className="shimmer h-7 w-24 rounded" />
          ) : best ? (
            <span className="font-mono text-2xl font-semibold" style={{ color: "var(--on-surface)" }}>
              {currencySymbol(best.currency)}
              {best.currency === "USD" ? best.price.toFixed(2) : best.price.toLocaleString("en-IN")}
            </span>
          ) : (
            <span className="text-label-md" style={{ color: "var(--outline)" }}>
              Unavailable
            </span>
          )}
        </div>

        {!pricesLoading && best && (
          <div className="flex gap-2">
            <a
              href={best.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-1 items-center justify-center gap-2 rounded-full px-4 py-2.5 text-label-lg transition-all"
              style={{ background: "var(--primary-container)", color: "var(--on-primary)" }}
            >
              View Deal on {best.marketplace}
              <ExternalLink size={14} />
            </a>
            {prices && prices.length > 1 && (
              <button
                onClick={() => setShowCompare((s) => !s)}
                className="rounded-full px-4 py-2.5 text-label-lg"
                style={{ border: "1px solid var(--outline-variant)", color: "var(--on-surface)" }}
              >
                Compare {prices.length} offers
              </button>
            )}
          </div>
        )}

        {showCompare && prices && (
          <div
            className="rounded-[var(--r-lg)] p-3"
            style={{ background: "var(--surface-container)" }}
          >
            <div className="flex flex-col gap-2">
              {prices.map((p) => (
                <div
                  key={p.marketplace}
                  className="flex items-center justify-between rounded-[var(--r-sm)] px-3 py-2"
                  style={{ opacity: p.availability === "out_of_stock" ? 0.4 : 1 }}
                >
                  <span className="text-body-md" style={{ color: "var(--on-surface)" }}>
                    {p.marketplace}
                  </span>
                  <div className="flex items-center gap-3">
                    <AvailabilityBadge availability={p.availability} />
                    <span className="font-mono text-sm" style={{ color: "var(--on-surface)" }}>
                      {currencySymbol(p.currency)}
                      {p.currency === "USD" ? p.price.toFixed(2) : p.price.toLocaleString("en-IN")}
                    </span>
                    <a href={p.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--outline)" }}>
                      <ExternalLink size={14} />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function AvailabilityBadge({ availability }: { availability: Price["availability"] }) {
  const map = {
    in_stock: { label: "In Stock", color: "#7fd089" },
    limited: { label: "Limited", color: "#f5a623" },
    out_of_stock: { label: "Unavailable", color: "#ffb4ab" },
  } as const;
  const m = map[availability];
  return (
    <span
      className="flex items-center gap-1.5 rounded-full px-2 py-0.5 text-label-sm"
      style={{ background: "var(--surface-high)", color: "var(--on-surface-variant)" }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: m.color }} />
      {m.label}
    </span>
  );
}
