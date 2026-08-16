import Image from "next/image";
import Link from "next/link";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { categories } from "@/lib/news";

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
      <div className="flex h-14 items-center justify-between px-4 md:px-6">
        <Link href="/" className="flex items-center gap-2">
          <Image src="/Frame 66.png" alt="Ai Bullet In" width={28} height={28} className="rounded-sm" />
          <span className="text-lg font-semibold tracking-tight">
            Ai Bullet In
          </span>
        </Link>

        <Sheet>
          <SheetTrigger
            render={<Button variant="outline" size="icon" aria-label="Open navigation" />}
          >
            <Menu />
          </SheetTrigger>
          <SheetContent side="right">
            <SheetHeader>
              <SheetTitle>Menu</SheetTitle>
            </SheetHeader>
            <Separator />
            <nav className="flex flex-col gap-1 px-4">
              {categories.map((category) => (
                <a
                  key={category}
                  href="#"
                  className="rounded-md px-2 py-2 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground"
                >
                  {category}
                </a>
              ))}
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
}
