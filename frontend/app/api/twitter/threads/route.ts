import { NextRequest, NextResponse } from "next/server";
import { getTwitterThreads } from "@/lib/data";

/** GET /api/twitter/threads - topic matches grouped with conversation replies. */
export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const limit = clamp(parseIntOr(params.get("limit"), 20), 1, 100);
  const offset = Math.max(parseIntOr(params.get("offset"), 0), 0);
  const searchQuery = params.get("search_query") ?? undefined;

  const threads = await getTwitterThreads({ searchQuery, limit, offset });
  return NextResponse.json(threads);
}

function parseIntOr(value: string | null, fallback: number): number {
  if (value === null) return fallback;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
