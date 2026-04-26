import { createFileRoute } from "@tanstack/react-router";
import { wrap, fail } from "@/server/mock";

export const Route = createFileRoute("/api/chat")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        try {
          const body = (await request.json()) as { session_id?: string; message?: string };
          if (!body.session_id || !body.message) {
            return Response.json(fail("INVALID_INPUT", "session_id and message required"), { status: 400 });
          }
          return Response.json(
            wrap({
              message: `Got it — I'll factor in: "${body.message}"`,
              updated_questions: null,
            })
          );
        } catch {
          return Response.json(fail("BAD_REQUEST", "Could not parse request"), { status: 400 });
        }
      },
    },
  },
});
