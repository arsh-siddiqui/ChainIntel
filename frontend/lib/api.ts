import type { Envelope } from "@/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public meta: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<{ data: T; meta: Record<string, unknown> }> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body;
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api${path}`, { method: options.method ?? "GET", headers, body, signal: options.signal });
  } catch {
    throw new ApiError("NETWORK_ERROR", "Cannot reach the ChainIntel backend. Is the API server running?", 0);
  }

  let envelope: Envelope<T> | null = null;
  try {
    envelope = (await response.json()) as Envelope<T>;
  } catch {
    /* non-JSON response */
  }

  if (!envelope || typeof envelope.success !== "boolean") {
    throw new ApiError("BAD_RESPONSE", "The server returned an unexpected response.", response.status);
  }
  if (!envelope.success || envelope.error) {
    const error = envelope.error ?? { code: "UNKNOWN", message: "Request failed." };
    throw new ApiError(error.code, error.message, response.status, envelope.meta ?? {});
  }
  return { data: envelope.data, meta: envelope.meta ?? {} };
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, form: FormData) => request<T>(path, { method: "POST", body: form }),
};

export function apiDownload(path: string, filename: string): void {
  const anchor = document.createElement("a");
  anchor.href = `${API_BASE}/api${path}`;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

export function explorerUrl(blockchain: string, address: string): string | null {
  switch (blockchain) {
    case "bitcoin":
      return `https://mempool.space/address/${address}`;
    case "ethereum":
      return `https://etherscan.io/address/${address}`;
    case "bsc":
      return `https://bscscan.com/address/${address}`;
    default:
      return null;
  }
}
