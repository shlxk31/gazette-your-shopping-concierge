import { createFileRoute } from "@tanstack/react-router";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

export const Route = createFileRoute("/api/products/$id/prices")({
  server: {
    handlers: {
      GET: async ({ params, request }) => {
        const incoming = new URL(request.url);
        const session_id = incoming.searchParams.get("session_id") ?? "";

        const upstream = `${BASE_URL}${API_PREFIX}/products/${params.id}/prices?session_id=${session_id}`;

        try {
          const resp = await fetch(upstream, {
            headers: { "Content-Type": "application/json" },
          });
          const json = await resp.json();
          return Response.json(json, { status: resp.status });
        } catch (err) {
          return Response.json(
            { success: false, error: { code: "UPSTREAM_ERROR", message: String(err) }, data: null },
            { status: 502 }
          );
        }
      },
    },
  },
});