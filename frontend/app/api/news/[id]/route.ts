import { NextRequest, NextResponse } from "next/server";
import { getArticleByIdCached } from "@/lib/data";

/** GET /api/news/[id] - a single RSS article by id. 404 if not found. */
export async function GET(
  _request: NextRequest,
  ctx: RouteContext<"/api/news/[id]">,
) {
  const { id } = await ctx.params;
  const numericId = Number(id);
  if (!Number.isInteger(numericId)) {
    return NextResponse.json({ detail: "Invalid article id" }, { status: 400 });
  }

  const article = await getArticleByIdCached(numericId);
  if (!article) {
    return NextResponse.json({ detail: "Article not found" }, { status: 404 });
  }
  return NextResponse.json(article);
}
