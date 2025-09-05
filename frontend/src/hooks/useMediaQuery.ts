import { useState, useEffect } from 'react';

export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setMatches(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [query]);

  return matches;
};

export const useBreakpoint = () => {
  const isMobile = useMediaQuery('(max-width: 767px)');
  const isTablet = useMediaQuery('(min-width: 768px) and (max-width: 1023px)');
  const isDesktop = useMediaQuery('(min-width: 1024px) and (max-width: 1439px)');
  const isLargeDesktop = useMediaQuery('(min-width: 1440px)');

  return {
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,
    currentBreakpoint: isMobile 
      ? 'mobile' 
      : isTablet 
        ? 'tablet' 
        : isDesktop 
          ? 'desktop' 
          : 'large-desktop'
  };
};