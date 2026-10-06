import { Header } from "@/components/header";

export default function Loading() {
  return (
    <>
      <Header active="x" />
      <div className="mx-auto grid h-[calc(100dvh-3.5rem)] w-full max-w-6xl grid-cols-1 overflow-hidden border-x lg:grid-cols-[minmax(0,1fr)_20rem]">
        <main className="border-r">
          <div className="border-b px-5 py-4">
            <div className="h-6 w-28 animate-pulse rounded-md bg-muted" />
            <div className="mt-2 h-4 w-52 animate-pulse rounded-md bg-muted" />
          </div>
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="flex gap-3 border-b px-5 py-5">
              <div className="size-10 shrink-0 animate-pulse rounded-full bg-muted" />
              <div className="min-w-0 flex-1 space-y-3">
                <div className="h-4 w-40 animate-pulse rounded bg-muted" />
                <div className="h-4 w-full animate-pulse rounded bg-muted" />
                <div className="h-4 w-4/5 animate-pulse rounded bg-muted" />
              </div>
            </div>
          ))}
        </main>
        <aside className="hidden p-5 lg:block">
          <div className="h-6 w-20 animate-pulse rounded bg-muted" />
          <div className="mt-6 space-y-5">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-16 animate-pulse rounded-xl bg-muted" />
            ))}
          </div>
        </aside>
      </div>
    </>
  );
}
