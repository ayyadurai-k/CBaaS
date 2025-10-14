import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/**
 * ScrollToTop Component
 * 
 * This component automatically scrolls the page to the top whenever the route changes.
 * It's a common solution for SPAs where scroll position is preserved between navigation.
 * 
 * Industry best practice for React Router applications.
 */
export const ScrollToTop = () => {
  const { pathname } = useLocation();

  useEffect(() => {
    // Scroll to top when pathname changes
    window.scrollTo(0, 0);
  }, [pathname]);

  // This component doesn't render anything
  return null;
};