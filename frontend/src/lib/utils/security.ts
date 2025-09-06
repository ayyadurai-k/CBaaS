// src/lib/utils/security.ts

/**
 * TokenStorage utility for managing authentication tokens
 * Provides a centralized interface for token operations
 */
export class TokenStorage {
  private static readonly ACCESS_TOKEN_KEY = 'access_token';
  private static readonly REFRESH_TOKEN_KEY = 'refresh_token';

  /**
   * Get the stored access token
   * @returns string | null - The access token or null if not found
   */
  static getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  /**
   * Get the stored refresh token
   * @returns string | null - The refresh token or null if not found
   */
  static getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Store both access and refresh tokens
   * @param accessToken - The access token to store
   * @param refreshToken - The refresh token to store
   */
  static setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  /**
   * Set only the access token (useful for token refresh)
   * @param accessToken - The access token to store
   */
  static setAccessToken(accessToken: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
  }

  /**
   * Set only the refresh token
   * @param refreshToken - The refresh token to store
   */
  static setRefreshToken(refreshToken: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  /**
   * Clear both access and refresh tokens
   */
  static clearTokens(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Check if user is authenticated (has access token)
   * @returns boolean - True if access token exists
   */
  static isAuthenticated(): boolean {
    return Boolean(this.getAccessToken());
  }

  /**
   * Get all tokens as an object
   * @returns object with access and refresh tokens
   */
  static getAllTokens(): { access: string | null; refresh: string | null } {
    return {
      access: this.getAccessToken(),
      refresh: this.getRefreshToken(),
    };
  }
}
