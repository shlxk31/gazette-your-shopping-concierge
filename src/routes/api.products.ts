import { createFileRoute } from "@tanstack/react-router";
import { wrap, fail, productsFor } from "@/server/mock";

export const Route = createFileRoute("/api/products")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const url = new URL(request.url);
        const session_id = url.searchParams.get("session_id");
        const category = url.searchParams.get("category") || "general";
        if (!session_id) {
          return Response.json(fail("INVALID_INPUT", "session_id is required"), { status: 400 });
        }
        return Response.json(wrap({ products: productsFor(category) }));
      },
    },
  },
});
