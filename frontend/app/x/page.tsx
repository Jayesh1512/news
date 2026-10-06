import type { Metadata } from "next";
import { Header } from "@/components/header";
import { XTimeline } from "@/components/x-timeline";
import { getTwitterThreads } from "@/lib/data";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "X Pulse · Ai Bullet In",
  description: "Topic-matched X conversations and their associated threads.",
};

export default async function XPage() {
  const threads = await getTwitterThreads({ limit: 100 });

  return (
    <>
      <Header active="x" />
      <XTimeline threads={threads} />
    </>
  );
}
