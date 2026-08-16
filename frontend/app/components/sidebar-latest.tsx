import Link from "next/link";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { getFeed } from "@/lib/news";

export async function SidebarLatest() {
  const feed = await getFeed(20);

  return (
    <aside className="hidden w-72 shrink-0 border-r md:block">
      <div className="sticky top-14 h-[calc(100vh-3.5rem)] px-1 py-4">
        <h2 className="text-sm font-semibold tracking-tight mx-2 text-muted-foreground">
          Latest News
        </h2>
        <ScrollArea className="h-[calc(100%-2.5rem)]">
          <ul className="flex flex-col pr-3">
            {feed.map((item, i) => (
              <li key={item.id}>
                <Link
                  href={item.href}
                  target={item.external ? "_blank" : undefined}
                  rel={item.external ? "noopener noreferrer" : undefined}
                  className="block rounded-md px-2 py-3 hover:bg-accent hover:text-accent-foreground"
                >
                  <p className="text-sm font-medium leading-snug">
                    {item.title}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {item.category} · {item.publishedAt}
                  </p>
                </Link>
                {i < feed.length - 1 && <Separator className="my-1" />}
              </li>
            ))}
          </ul>
        </ScrollArea>
      </div>
    </aside>
  );
}
