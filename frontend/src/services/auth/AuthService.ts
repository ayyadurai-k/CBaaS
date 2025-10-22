// src/services/auth/AuthService.ts
import { LoginAPI, LoginPayload, LoginResponse } from "../../apis/auth/LoginAPI";
import { SignupAPI, SignupPayload, SignupResponse } from "../../apis/auth/SignupAPI";
import { LogoutAPI } from "../../apis/auth/LogoutAPI";
import { ResetAPI, ForgotPasswordPayload, VerifyResetTokenPayload, ResetPasswordPayload } from "../../apis/auth/ResetAPI";
import { getErrorMessage } from "../../apis/configs/axiosUtils";

export type AuthUser = {
  id: string;
  email: string;
  name: string;
  full_name: string;
};

export type LoginResult = {
  success: boolean;
  user?: AuthUser;
  message?: string;
};

export type SignupResult = {
  success: boolean;
  user?: AuthUser;
  message?: string;
};

export class AuthService {
  private readonly ACCESS_TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';

  async login(payload: LoginPayload): Promise<LoginResult> {
    try {
      const { data } = await LoginAPI.login(payload);
      
      // Store tokens in localStorage
      localStorage.setItem(this.ACCESS_TOKEN_KEY, data.access);
      localStorage.setItem(this.REFRESH_TOKEN_KEY, data.refresh);
      
      const user: AuthUser = {
        ...data.user,
        full_name: data.user.name,
      };
      
      return { success: true, user };
    } catch (error: any) {
      // Use global error handler utility - parses backend {error, detail, type} format
      return {
        success: false,
        message: getErrorMessage(error, 'Login failed'),
      };
    }
  }

  async signup(payload: SignupPayload): Promise<SignupResult> {
    try {
      const { data } = await SignupAPI.signup(payload);
      
      // Store tokens in localStorage
      localStorage.setItem(this.ACCESS_TOKEN_KEY, data.access);
      localStorage.setItem(this.REFRESH_TOKEN_KEY, data.refresh);
      
      // Since backend doesn't return user data, create a basic user object
      const user: AuthUser = {
        id: '', // Will be populated when user data is fetched
        email: payload.email,
        name: payload.name,
        full_name: payload.name,
      };
      
      return { success: true, user, message: 'Account created successfully!' };
    } catch (error: any) {
      // Use global error handler utility - parses backend {error, detail, type} format
      return {
        success: false,
        message: getErrorMessage(error, 'Signup failed'),
      };
    }
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
      if (refreshToken) {
        await LogoutAPI.logout({ refresh: refreshToken });
      }
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      // Clear local tokens
      localStorage.removeItem(this.ACCESS_TOKEN_KEY);
      localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    }
  }

  async forgotPassword(payload: ForgotPasswordPayload): Promise<{ success: boolean; message: string }> {
    try {
      const { data } = await ResetAPI.forgotPassword(payload);
      return { success: true, message: data.message };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to send reset email',
      };
    }
  }

  async verifyResetToken(payload: VerifyResetTokenPayload): Promise<{ valid: boolean; message: string }> {
    try {
      const { data } = await ResetAPI.verifyResetToken(payload);
      return { valid: data.valid, message: data.message };
    } catch (error: any) {
      return {
        valid: false,
        message: error.response?.data?.message || 'Invalid token',
      };
    }
  }

  async resetPassword(payload: ResetPasswordPayload): Promise<{ success: boolean; message: string }> {
    try {
      const { data } = await ResetAPI.resetPassword(payload);
      return { success: true, message: data.message };
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to reset password',
      };
    }
  }

  isAuthenticated(): boolean {
    return Boolean(localStorage.getItem(this.ACCESS_TOKEN_KEY));
  }

  getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
      if (!refreshToken) return false;

      const { data } = await LoginAPI.refreshToken({ refresh: refreshToken });
      localStorage.setItem(this.ACCESS_TOKEN_KEY, data.access);
      return true;
    } catch (error) {
      // Clear tokens if refresh fails
      this.logout();
      return false;
    }
  }
}

// Singleton instance for app-wide usage
export const authService = new AuthService();
