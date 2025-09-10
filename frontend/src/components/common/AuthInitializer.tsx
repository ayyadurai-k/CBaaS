import React, { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/redux/useAuth';
import { Loader2 } from 'lucide-react';

interface AuthInitializerProps {
  children: React.ReactNode;
}

export const AuthInitializer: React.FC<AuthInitializerProps> = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const { checkAuthStatus, isLoading } = useAuth();

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        await checkAuthStatus();
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsInitialized(true);
      }
    };

    initializeAuth();
  }, [checkAuthStatus]);

  if (!isInitialized || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Initializing application...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
