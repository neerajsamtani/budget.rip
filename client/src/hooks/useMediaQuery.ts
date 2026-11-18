import { useEffect, useState } from 'react';

/** Whether a CSS media query matches, updating only when the answer changes (not on every resize). */
export function useMediaQuery(query: string): boolean {
  // Read it up front so the first render already picks the right layout.
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const update = () => setMatches(mediaQuery.matches);
    update();
    mediaQuery.addEventListener('change', update);
    return () => mediaQuery.removeEventListener('change', update);
  }, [query]);

  return matches;
}
