import { NextResponse } from "next/server";

const BACKEND_URL = (process.env.BACKEND_URL ?? "http://localhost:8501").replace(/\/$/, "");

/** Keep credentials server-side while forwarding an interactive topic search. */
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "The request body must be valid JSON." }, { status: 400 });
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/twitter/topic-searches`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const payload = await response.json().catch(() => ({ detail: "The backend returned an unreadable response." }));
    return NextResponse.json(payload, { status: response.status });
  } catch {
    return NextResponse.json(
      { detail: "The backend is unavailable. Start the API and try again." },
      { status: 503 },
    );
  }
}
