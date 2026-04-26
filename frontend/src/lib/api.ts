import type { ApiResponse } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL
const API_PREFIX = "/api/v1"

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
  console.log(`${BASE_URL}${API_PREFIX}${url}`)
  const res = await fetch(`${BASE_URL}${API_PREFIX}${url}`, {
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
