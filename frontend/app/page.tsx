import Link from "next/link";
import { Header } from "@/components/header";
import { SidebarLatest } from "@/components/sidebar-latest";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getFeed } from "@/lib/news";

export default async function Page() {
  const feed = await getFeed();

  if (feed.length === 0) {
    return (
      <>
        <Header />
        <div className="flex flex-1">
          <SidebarLatest />
          <main className="flex-1 px-4 py-6 md:px-8">
            <p className="text-muted-foreground">
              No articles yet. Check back soon, or trigger a manual scrape
              from the backend.
            </p>
          </main>
        </div>
      </>
    );
  }

  const [featured, ...rest] = feed;

  return (
    <>
      <Header />
      <div className="flex flex-1">
        <SidebarLatest />
        <main className="flex-1 px-4 py-6 md:px-8">
          <Link
            href={featured.href}
            target={featured.external ? "_blank" : undefined}
            rel={featured.external ? "noopener noreferrer" : undefined}
            className="block mb-8"
          >
            <Card className="p-8 hover:bg-accent/50">
              <CardHeader className="p-0">
                <Badge className="w-fit">{featured.category}</Badge>
                <CardTitle className="mt-3 text-3xl md:text-4xl">
                  {featured.title}
                </CardTitle>
                <CardDescription className="mt-2 text-base">
                  {featured.excerpt}
                </CardDescription>
              </CardHeader>
              <CardFooter className="mt-4 p-0 text-sm text-muted-foreground">
                {featured.author} · {featured.publishedAt}
              </CardFooter>
            </Card>
          </Link>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {rest.map((item) => (
              <Link
                key={item.id}
                href={item.href}
                target={item.external ? "_blank" : undefined}
                rel={item.external ? "noopener noreferrer" : undefined}
              >
                <Card className="h-full hover:bg-accent/50">
                  <CardHeader>
                    <Badge variant="secondary" className="w-fit">
                      {item.category}
                    </Badge>
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                    <CardDescription>{item.excerpt}</CardDescription>
                  </CardHeader>
                  <CardFooter className="text-xs text-muted-foreground">
                    {item.author} · {item.publishedAt}
                  </CardFooter>
                </Card>
              </Link>
            ))}
          </div>
        </main>
      </div>
    </>
  );
}
