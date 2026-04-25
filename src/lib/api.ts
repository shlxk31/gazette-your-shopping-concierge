import type { ApiResponse } from "./types";

export class ApiError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

export async function api<T>(
  url: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  const json = (await res.json()) as ApiResponse<T>;
  if (!json.success || json.data === null) {
    const msg = json.error?.message || "Something went wrong";
    throw new ApiError(json.error?.code || "UNKNOWN", msg);
  }
  return json.data;
}
