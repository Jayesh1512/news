import type { Metadata } from "next";
import { Header } from "@/components/header";
import { XProfileDirectory } from "@/components/x-profile-directory";
import { getTwitterProfiles } from "@/lib/data";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "People · X Pulse · Ai Bullet In",
  description: "Topic-matched people, profile summaries, and supporting X posts.",
};

export default async function XProfilesPage() {
  const profiles = await getTwitterProfiles({ limit: 500 });

  return (
    <>
      <Header active="x" />
      <XProfileDirectory profiles={profiles} />
    </>
  );
}
