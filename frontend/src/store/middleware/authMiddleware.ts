/**
 * Auth Middleware
 *
 * Handles automatic token refresh and logout on auth failures.
 * Intercepts API calls that return 401 and attempts token refresh.
 */

import { Middleware, isRejectedWithValue } from "@reduxjs/toolkit";
import { logout } from "../slices/authSlice";
import { clearProfile } from "../slices/userSlice";
import { resetUIState } from "../slices/uiSlice";
import { loginThunk } from "../services/authApi";
import { toast } from "@/hooks/use-toast";

export const authMiddleware: Middleware =
  (store) => (next) => (action: any) => {
    // Handle auth failures
    if (isRejectedWithValue(action)) {
      const payload = action.payload as any;
      if (payload?.status === 401) {
        // Dispatch logout actions
        store.dispatch(logout());
        store.dispatch(clearProfile());
        store.dispatch(resetUIState());

        // Show error toast
        toast({
          title: "Session Expired",
          description: "Please log in again to continue.",
          variant: "destructive",
        });

        // Redirect to login (you might want to handle this differently)
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }

    // Handle successful auth actions
    if (action.type === loginThunk.fulfilled.type) {
      console.log("Auth Middleware Action loginThunk:", action);
      toast({
        title: "Welcome back!",
        description: "You have successfully logged in.",
      });
    }

    if (action.type === "auth/logout") {
      toast({
        title: "Logged out",
        description: "You have been successfully logged out.",
      });
    }

    return next(action);
  };
