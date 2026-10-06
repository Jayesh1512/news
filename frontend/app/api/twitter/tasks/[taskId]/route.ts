import { NextResponse } from "next/server";

const BACKEND_URL = (process.env.BACKEND_URL ?? "http://localhost:8501").replace(/\/$/, "");

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ taskId: string }> },
) {
  const { taskId } = await params;
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/twitter/tasks/${encodeURIComponent(taskId)}`,
      { cache: "no-store" },
    );
    const payload = await response.json().catch(() => ({ detail: "The backend returned an unreadable response." }));
    return NextResponse.json(payload, { status: response.status });
  } catch {
    return NextResponse.json(
      { detail: "The backend is unavailable. Start the API and try again." },
      { status: 503 },
    );
  }
}
