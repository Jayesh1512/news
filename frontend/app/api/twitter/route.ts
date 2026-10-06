import { NextRequest, NextResponse } from "next/server";
import { getTwitterPosts } from "@/lib/data";

/**
 * GET /api/twitter
 *
 * Query params: account, limit (1-100, default 20), offset (default 0).
 *
 * Reads from FastAPI's JSON-backed Twitter collection (see app/lib/data.ts),
 * cached for 60 seconds.
 */
export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;

  const limit = clamp(parseIntOr(params.get("limit"), 20), 1, 100);
  const offset = Math.max(parseIntOr(params.get("offset"), 0), 0);
  const account = params.get("account") ?? undefined;
  const searchQuery = params.get("search_query") ?? undefined;

  const posts = await getTwitterPosts({ account, searchQuery, limit, offset });
  return NextResponse.json(posts);
}

function parseIntOr(value: string | null, fallback: number): number {
  if (value === null) return fallback;
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) ? n : fallback;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
