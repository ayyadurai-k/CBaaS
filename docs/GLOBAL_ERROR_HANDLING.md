# Global Error Handling - Best Practices Implementation

## Overview

This project implements **industry-standard global error handling** for API errors using **Axios Response Interceptors**. This ensures consistent error messages across the entire application.

## Architecture

### Backend (Django)
- **Global Exception Handler**: `backend/common/exceptions/handlers.py`
- **Error Format**: 
  ```json
  {
    "error": "User-friendly error message",
    "detail": "Additional details (optional)",
    "type": "ErrorType"
  }
  ```

### Frontend (React/TypeScript)
- **Axios Interceptor**: `frontend/src/apis/configs/axiosConfig.ts`
- **Error Utilities**: `frontend/src/apis/configs/axiosUtils.ts`

## How It Works

### 1. Backend Returns Standardized Errors
All backend errors are caught and transformed by the global exception handler:

```python
# IntegrityError example
{
  "error": "This email address is already registered.",
  "detail": "This email address is already registered.",
  "type": "IntegrityError"
}
```

### 2. Axios Interceptor Parses Errors
The response interceptor automatically parses all API errors:

```typescript
// In axiosConfig.ts
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Parse backend error format
    if (error.response?.data) {
      const backendError = error.response.data;
      error.userMessage = backendError.error || backendError.message || 'An error occurred';
      error.errorType = backendError.type;
      error.errorDetail = backendError.detail;
    }
    return Promise.reject(error);
  }
);
```

### 3. Components Use Simple Error Handling

**✅ Recommended Pattern:**
```typescript
import { getErrorMessage } from '@/apis/configs/axiosUtils';

try {
  await api.post('/signup', data);
} catch (error) {
  const message = getErrorMessage(error);
  toast.error(message); // Shows: "This email address is already registered."
}
```

**❌ Old Pattern (Don't Use):**
```typescript
// BAD - Manual error parsing in every component
const errorMessage = error?.response?.data?.error || 
                     error?.response?.data?.message || 
                     'An error occurred';
```

## Utility Functions

### `getErrorMessage(error, fallback?)`
Extract user-friendly error message from any error.

```typescript
const message = getErrorMessage(error, 'Custom fallback message');
toast.error(message);
```

### `getErrorDetails(error)`
Get detailed error information for debugging.

```typescript
const details = getErrorDetails(error);
console.error('Error details:', details);
// {
//   message: "This email address is already registered.",
//   type: "IntegrityError",
//   status: 400,
//   statusText: "Bad Request"
// }
```

### `isErrorStatus(error, status)`
Check if error is a specific HTTP status.

```typescript
if (isErrorStatus(error, 404)) {
  toast.error('Resource not found');
}
```

### `isNetworkError(error)`
Check if error is a network error (no server response).

```typescript
if (isNetworkError(error)) {
  toast.error('Network error. Please check your connection.');
}
```

## Migration Guide

### Before (Manual Error Parsing)
```typescript
catch (error: unknown) {
  const errorData = (error as { response?: { data?: { error?: string } } })?.response?.data;
  const errorMessage = errorData?.error || errorData?.message || 'An error occurred';
  toast.error(errorMessage);
}
```

### After (Global Error Handler)
```typescript
import { getErrorMessage } from '@/apis/configs/axiosUtils';

catch (error: unknown) {
  const errorMessage = getErrorMessage(error);
  toast.error(errorMessage);
}
```

## Benefits

✅ **DRY Principle** - Error parsing in one place  
✅ **Type Safety** - TypeScript interfaces for error properties  
✅ **Consistency** - All errors handled the same way  
✅ **Maintainability** - Easy to update error format  
✅ **User Experience** - Clear, user-friendly messages  
✅ **Developer Experience** - Simple API, less boilerplate  

## Examples in Codebase

- ✅ **SignupPage**: `frontend/src/components/auth/SignupPage.tsx`
- ✅ **AuthService**: `frontend/src/services/auth/AuthService.ts`

## Error Type Mapping

| Backend Error | HTTP Status | User Message |
|--------------|-------------|--------------|
| `IntegrityError` (duplicate email) | 400 | "This email address is already registered." |
| `IntegrityError` (duplicate slug) | 400 | "An organization with this name already exists..." |
| `ValidationError` | 400 | Specific field validation message |
| `PermissionDenied` | 403 | "You don't have permission to perform this action." |
| `Http404` | 404 | "The requested resource was not found." |
| Generic Exception | 500 | "An internal server error occurred." |

## Testing

Test error handling in Postman:

```bash
# Test duplicate email
POST http://localhost:8000/api/auth/signup
{
  "email": "existing@example.com",
  ...
}

# Expected Response (400):
{
  "error": "This email address is already registered.",
  "detail": "This email address is already registered.",
  "type": "IntegrityError"
}
```

Frontend will automatically show: **"This email address is already registered."** ✅

## Future Enhancements

- [ ] Add error tracking (Sentry integration)
- [ ] Add retry logic for network errors
- [ ] Add offline detection
- [ ] Add error analytics
- [ ] Add toast notification patterns (success/info/warning/error)
