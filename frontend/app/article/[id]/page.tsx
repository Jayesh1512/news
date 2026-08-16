import { notFound } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/header";
import { SidebarLatest } from "@/components/sidebar-latest";
import { Badge } from "@/components/ui/badge";
import { getArticleById } from "@/lib/news";

function formatDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default async function ArticlePage(props: PageProps<"/article/[id]">) {
  const { id } = await props.params;
  const article = await getArticleById(id);

  if (!article) notFound();

  const plainContent = (article.content ?? "").replace(/<[^>]*>/g, "").trim();

  return (
    <>
      <Header />
      <div className="flex flex-1">
        <SidebarLatest />
        <main className="flex-1 px-4 py-6 md:px-8">
          <article className="mx-auto max-w-2xl">
            <Badge className="w-fit">{article.category ?? article.source}</Badge>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              {article.title}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {article.author ?? article.source} ·{" "}
              {formatDate(article.published_at ?? article.fetched_at)}
            </p>
            <p className="mt-6 text-base leading-relaxed text-foreground">
              {plainContent || "No summary available for this article."}
            </p>
            <Link
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6 inline-block text-sm font-medium text-primary underline underline-offset-4"
            >
              Read full article at {article.source} →
            </Link>
          </article>
        </main>
      </div>
    </>
  );
}
