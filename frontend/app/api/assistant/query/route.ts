import { NextRequest, NextResponse } from "next/server";

import { proxyBackend } from "@/lib/backend-proxy";

export const dynamic = "force-dynamic";

function getQuestion(payload: unknown) {
  if (!payload || typeof payload !== "object") {
    return "";
  }

  const question = (payload as { question?: unknown }).question;
  return typeof question === "string" ? question.trim() : "";
}

export async function POST(request: NextRequest) {
  const payload = await request.json().catch(() => null);
  const question = getQuestion(payload);

  if (!question) {
    return NextResponse.json(
      { detail: "Question is required." },
      { status: 400 },
    );
  }

  return proxyBackend("/api/assistant/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
