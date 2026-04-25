import { createFileRoute } from "@tanstack/react-router";
import { wrap, fail, nextQuestionsFor } from "@/server/mock";

// Trivial in-memory session counter; on serverless this won't persist between
// instances, so the client also tracks its own progress. Used only to decide
// when to mark is_complete = true (after 2 batches).
const batchCounts = new Map<string, number>();

export const Route = createFileRoute("/api/questions/answer")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        try {
          const body = (await request.json()) as {
            session_id?: string;
            answers?: Array<{ question_id: string; value: any }>;
            category?: string;
            batch?: number;
          };
          if (!body.session_id) {
            return Response.json(fail("INVALID_INPUT", "session_id is required"), { status: 400 });
          }
          const batch = body.batch ?? (batchCounts.get(body.session_id) || 0) + 1;
          batchCounts.set(body.session_id, batch);
          const category = body.category || "general";

          if (batch >= 2) {
            return Response.json(
              wrap({ next_questions: null, is_complete: true, redirect_to: "/results" })
            );
          }
          return Response.json(
            wrap({
              next_questions: nextQuestionsFor(category),
              is_complete: false,
              redirect_to: null,
            })
          );
        } catch {
          return Response.json(fail("BAD_REQUEST", "Could not parse request"), { status: 400 });
        }
      },
    },
  },
});
