import { NextRequest, NextResponse } from "next/server";
import { getArticles } from "@/lib/data";

/**
 * GET /api/news
 *
 * Query params: source, category, limit (1-100, default 20),
 * offset (default 0), hours (1-168, default 24).
 *
 * Reads directly from Supabase (see app/lib/data.ts), cached for 60s via
 * `unstable_cache` so bursts of requests don't each hit the database.
 */
export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;

  const limit = clamp(parseIntOr(params.get("limit"), 20), 1, 100);
  const offset = Math.max(parseIntOr(params.get("offset"), 0), 0);
  const hours = clamp(parseIntOr(params.get("hours"), 24), 1, 168);
  const source = params.get("source") ?? undefined;
  const category = params.get("category") ?? undefined;

  const articles = await getArticles({ source, category, limit, offset, hours });
  return NextResponse.json(articles);
}

function parseIntOr(value: string | null, fallback: number): number {
  if (value === null) return fallback;
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) ? n : fallback;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
