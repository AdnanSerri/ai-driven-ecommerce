import { useState, useEffect } from "react";

/**
 * Returns false during SSR and on the first client render (to match the server),
 * then true after hydration completes.
 * Use this to defer rendering that depends on client-only state (localStorage, etc.)
 */
export function useHydration() {
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  return hydrated;
}
