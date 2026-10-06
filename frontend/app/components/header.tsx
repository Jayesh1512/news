import Image from "next/image";
import Link from "next/link";
import { Menu, Newspaper, Radio } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";

type HeaderProps = {
  active?: "news" | "x";
};

const destinations = [
  { href: "/", label: "News", icon: Newspaper, key: "news" },
  { href: "/x", label: "X Pulse", icon: Radio, key: "x" },
] as const;

export function Header({ active = "news" }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
      <div className="flex h-14 items-center justify-between px-4 md:px-6">
        <Link href="/" className="flex items-center gap-2">
          <Image src="/Frame 66.png" alt="Ai Bullet In" width={28} height={28} className="rounded-sm" />
          <span className="text-lg font-semibold tracking-tight">
            Ai Bullet In
          </span>
        </Link>

        <nav aria-label="Primary navigation" className="hidden items-center gap-1 sm:flex">
          {destinations.map(({ href, label, icon: Icon, key }) => (
            <Link
              key={href}
              href={href}
              aria-current={active === key ? "page" : undefined}
              className={`flex h-8 items-center gap-2 rounded-lg px-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                active === key
                  ? "bg-primary/12 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <Icon className="size-4" aria-hidden="true" />
              {label}
            </Link>
          ))}
        </nav>

        <Sheet>
          <SheetTrigger
            render={<Button variant="outline" size="icon" aria-label="Open navigation" className="sm:hidden" />}
          >
            <Menu />
          </SheetTrigger>
          <SheetContent side="right">
            <SheetHeader>
              <SheetTitle>Menu</SheetTitle>
            </SheetHeader>
            <Separator />
            <nav aria-label="Mobile navigation" className="flex flex-col gap-1 px-4">
              {destinations.map(({ href, label, icon: Icon, key }) => (
                <Link
                  key={href}
                  href={href}
                  aria-current={active === key ? "page" : undefined}
                  className={`flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors ${
                    active === key
                      ? "bg-primary/12 text-primary"
                      : "text-foreground hover:bg-accent"
                  }`}
                >
                  <Icon className="size-4" aria-hidden="true" />
                  {label}
                </Link>
              ))}
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
}
