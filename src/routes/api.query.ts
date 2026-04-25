import { createFileRoute } from "@tanstack/react-router";
import { wrap, fail, detectCategory, initialQuestionsFor } from "@/server/mock";

export const Route = createFileRoute("/api/query")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        try {
          const body = (await request.json()) as { query?: string };
          const query = (body.query || "").trim();
          if (!query) {
            return Response.json(fail("INVALID_INPUT", "Query is required", "query"), { status: 400 });
          }
          const category = detectCategory(query);
          const session_id = "sess_" + Math.random().toString(36).slice(2, 10);
          return Response.json(
            wrap({
              session_id,
              detected_category: category,
              initial_questions: initialQuestionsFor(category),
              mode: "basic",
              query,
            })
          );
        } catch {
          return Response.json(fail("BAD_REQUEST", "Could not parse request"), { status: 400 });
        }
      },
    },
  },
});
