import { NextResponse } from "next/server";

import { getBackendApiBaseUrl } from "@/lib/team-api";

async function readBackendPayload(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      return (await response.json()) as unknown;
    } catch {
      return null;
    }
  }

  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { detail: text };
  }
}

export async function proxyBackend(path: string, init?: RequestInit) {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");

  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    const response = await fetch(`${getBackendApiBaseUrl()}${path}`, {
      ...init,
      cache: "no-store",
      headers,
    });
    const payload = await readBackendPayload(response);

    if (payload === null) {
      return new NextResponse(null, { status: response.status });
    }

    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      {
        detail:
          error instanceof Error ? error.message : "Backend request failed.",
      },
      { status: 502 },
    );
  }
}
