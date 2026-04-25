import { createFileRoute } from "@tanstack/react-router";
import { wrap, pricesFor } from "@/server/mock";

export const Route = createFileRoute("/api/products/$id/prices")({
  server: {
    handlers: {
      GET: async ({ params }) => {
        // small artificial delay to surface the skeleton state
        await new Promise((r) => setTimeout(r, 400));
        return Response.json(wrap({ prices: pricesFor(params.id) }));
      },
    },
  },
});
