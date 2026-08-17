// Server-only Supabase client. Uses the service_role key, so this file must
// never be imported from a Client Component or exposed to the browser - the
// `server-only` import throws a build error if that ever happens.
import "server-only";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

export function isSupabaseConfigured(): boolean {
  return Boolean(supabaseUrl && supabaseKey);
}

let cachedClient: SupabaseClient | null = null;

/** Lazily-created singleton Supabase client (service_role, bypasses RLS). */
export function getSupabaseClient(): SupabaseClient {
  if (!isSupabaseConfigured()) {
    throw new Error(
      "Supabase is not configured: set SUPABASE_URL and SUPABASE_KEY in frontend/.env.local (see frontend/.env.example).",
    );
  }
  if (!cachedClient) {
    cachedClient = createClient(supabaseUrl!, supabaseKey!, {
      auth: { persistSession: false },
    });
  }
  return cachedClient;
}
