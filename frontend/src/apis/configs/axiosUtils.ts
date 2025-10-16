// src/apis/configs/axiosUtils.ts
import { AxiosError } from 'axios';

/**
 * Extract user-friendly error message from API error
 * Works with the axios response interceptor that parses backend errors
 * 
 * @param error - The error object from catch block
 * @param fallback - Default message if no error message found
 * @returns User-friendly error message
 * 
 * @example
 * ```typescript
 * try {
 *   await api.post('/signup', data);
 * } catch (error) {
 *   const message = getErrorMessage(error);
 *   toast.error(message);
 * }
 * ```
 */
export const getErrorMessage = (error: unknown, fallback = 'An unexpected error occurred'): string => {
  // Check if it's an AxiosError with our parsed userMessage
  if (error && typeof error === 'object' && 'userMessage' in error) {
    return (error as AxiosError).userMessage || fallback;
  }
  
  // Fallback to response data error/message
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as AxiosError;
    const data = axiosError.response?.data as { error?: string; message?: string } | undefined;
    
    if (data?.error) return data.error;
    if (data?.message) return data.message;
  }
  
  // Fallback to error message property
  if (error && typeof error === 'object' && 'message' in error) {
    return (error as Error).message;
  }
  
  return fallback;
};

/**
 * Get detailed error information for debugging
 * 
 * @param error - The error object
 * @returns Object with error details
 */
export const getErrorDetails = (error: unknown) => {
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as AxiosError;
    
    return {
      message: (axiosError as any).userMessage || 'Unknown error',
      type: (axiosError as any).errorType,
      detail: (axiosError as any).errorDetail,
      status: axiosError.response?.status,
      statusText: axiosError.response?.statusText,
    };
  }
  
  return {
    message: error instanceof Error ? error.message : 'Unknown error',
    type: 'UnknownError',
  };
};

/**
 * Check if error is a specific HTTP status code
 * 
 * @param error - The error object
 * @param status - HTTP status code to check
 * @returns boolean
 */
export const isErrorStatus = (error: unknown, status: number): boolean => {
  if (error && typeof error === 'object' && 'response' in error) {
    return (error as AxiosError).response?.status === status;
  }
  return false;
};

/**
 * Check if error is a network error (no response from server)
 * 
 * @param error - The error object
 * @returns boolean
 */
export const isNetworkError = (error: unknown): boolean => {
  if (error && typeof error === 'object' && 'response' in error) {
    return !(error as AxiosError).response;
  }
  return false;
};
