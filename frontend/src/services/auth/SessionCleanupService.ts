/**
 * Session Cleanup Service
 * 
 * Handles complete session cleanup when organization is deleted
 * or when user needs to be forcefully logged out
 */

import { TokenStorage } from '@/lib/utils/security';

export class SessionCleanupService {
  /**
   * Perform complete session cleanup
   * Clears all tokens, localStorage data, and optionally redirects
   */
  static async performCompleteCleanup(options?: {
    redirectUrl?: string;
    showMessage?: boolean;
    clearAll?: boolean;
  }): Promise<void> {
    try {
      // Clear authentication tokens
      TokenStorage.clearTokens();
      
      if (options?.clearAll) {
        // Clear all localStorage except for essential app preferences
        const keysToPreserve = ['theme', 'language', 'ui-preferences'];
        const allKeys = Object.keys(localStorage);
        
        for (const key of allKeys) {
          if (!keysToPreserve.includes(key)) {
            localStorage.removeItem(key);
          }
        }
        
        // Clear sessionStorage
        sessionStorage.clear();
      } else {
        // Clear specific user/org related data
        const userDataKeys = [
          'user-profile',
          'organization-data', 
          'api-keys',
          'recent-documents',
          'chat-history',
          'user-preferences'
        ];
        
        userDataKeys.forEach(key => {
          localStorage.removeItem(key);
          sessionStorage.removeItem(key);
        });
      }
      
      // Clear any cached API data
      if (typeof window !== 'undefined') {
        // Clear any cached fetch responses
        if ('caches' in window) {
          try {
            const cacheNames = await caches.keys();
            await Promise.all(
              cacheNames.map(name => caches.delete(name))
            );
          } catch (error) {
            console.warn('Failed to clear caches:', error);
          }
        }
      }
      
      // Redirect if specified
      if (options?.redirectUrl && typeof window !== 'undefined') {
        setTimeout(() => {
          window.location.href = options.redirectUrl!;
        }, 100);
      }
      
    } catch (error) {
      console.error('Error during session cleanup:', error);
      
      // Force redirect even if cleanup fails
      if (options?.redirectUrl && typeof window !== 'undefined') {
        window.location.href = options.redirectUrl;
      }
    }
  }
  
  /**
   * Quick cleanup for organization deletion
   */
  static async cleanupAfterOrganizationDeletion(): Promise<void> {
    await this.performCompleteCleanup({
      redirectUrl: '/login',
      clearAll: true,
      showMessage: false
    });
  }
  
  /**
   * Standard logout cleanup
   */
  static async cleanupAfterLogout(): Promise<void> {
    await this.performCompleteCleanup({
      redirectUrl: '/login',
      clearAll: false
    });
  }
}