import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/redux/useAuth';

interface PublicRouteProps {
  children: React.ReactNode;
}

export const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();

  // Don't show loading state for public routes
  // Let the individual components (like LoginPage) handle their own loading states
  // This prevents full-page loaders from interrupting the UX during login

  if (isAuthenticated) {
    // If user is already authenticated, redirect to dashboard
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};
