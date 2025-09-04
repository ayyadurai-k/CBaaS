import React, { useState, useEffect } from 'react';
import { MessageSquare, Eye, EyeOff, AlertCircle, Loader2, CheckCircle2, Lock, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '@/services/auth/AuthService';

export const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  const email = searchParams.get('email');

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isValidating, setIsValidating] = useState(true);
  const [isValidToken, setIsValidToken] = useState(false);
  const [touchedFields, setTouchedFields] = useState<{[key: string]: boolean}>({});

  // Validate token on component mount
  useEffect(() => {
    const validateToken = async () => {
      if (!token || !email) {
        setErrors({ general: 'Invalid reset link. Please request a new password reset.' });
        setIsValidating(false);
        return;
      }

      try {
        const result = await authService.verifyResetToken({ token, email });
        if (result.valid) {
          setIsValidToken(true);
        } else {
          setErrors({ general: result.message || 'This reset link has expired or is invalid. Please request a new one.' });
        }
      } catch (error) {
        setErrors({ general: 'Unable to verify reset link. Please try again.' });
      } finally {
        setIsValidating(false);
      }
    };

    validateToken();
  }, [token, email]);

  // Real-time field validation
  const validateField = (name: string, value: string): string => {
    if (name === 'password') {
      if (!value) return 'Password is required';
      if (value.length < 8) return 'Password must be at least 8 characters';
      if (!/(?=.*[a-z])/.test(value)) return 'Password must contain at least one lowercase letter';
      if (!/(?=.*[A-Z])/.test(value)) return 'Password must contain at least one uppercase letter';
      if (!/(?=.*\d)/.test(value)) return 'Password must contain at least one number';
    }
    if (name === 'confirmPassword') {
      if (!value) return 'Please confirm your password';
      if (value !== formData.password) return 'Passwords do not match';
    }
    return '';
  };

  // Handle input changes with real-time validation
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    
    // Only show errors if the field has been touched
    if (touchedFields[name]) {
      const error = validateField(name, value);
      setErrors(prev => ({ ...prev, [name]: error }));
    }

    // Also validate confirm password if password changes
    if (name === 'password' && touchedFields.confirmPassword) {
      const confirmError = validateField('confirmPassword', formData.confirmPassword);
      setErrors(prev => ({ ...prev, confirmPassword: confirmError }));
    }
  };

  // Mark field as touched when it loses focus
  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setTouchedFields(prev => ({ ...prev, [name]: true }));
    const error = validateField(name, value);
    setErrors(prev => ({ ...prev, [name]: error }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token || !email) return;
    
    // Mark all fields as touched
    setTouchedFields({ password: true, confirmPassword: true });
    
    // Validate all fields
    const newErrors: {[key: string]: string} = {};
    Object.entries(formData).forEach(([key, value]) => {
      const error = validateField(key, value as string);
      if (error) newErrors[key] = error;
    });

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Clear any previous errors
    setErrors({});
    setIsLoading(true);

    try {
      const result = await authService.resetPassword({
        token,
        email,
        new_password: formData.password
      });
      
      if (result.success) {
        setIsSuccess(true);
        // Redirect to login after 3 seconds
        setTimeout(() => {
          navigate('/login?message=password-reset-success');
        }, 3000);
      } else {
        if (result.message?.toLowerCase().includes('expired') || result.message?.toLowerCase().includes('invalid')) {
          setErrors({ general: 'This reset link has expired or is invalid. Please request a new password reset.' });
        } else {
          setErrors({ general: result.message || 'Failed to reset password. Please try again.' });
        }
      }
    } catch (error) {
      setErrors({ general: 'Network error. Please check your connection and try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  // Loading state while validating token
  if (isValidating) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6 sm:p-10 transition-all duration-300">
            <div className="text-center">
              <div className="inline-flex items-center justify-center bg-blue-600 rounded-xl mx-auto mb-6 w-16 h-16 shadow-md">
                <Loader2 className="text-white w-8 h-8 animate-spin" />
              </div>
              <h1 className="font-bold text-slate-900 text-2xl mb-2">
                Validating Reset Link
              </h1>
              <p className="text-slate-600 text-base">
                Please wait while we verify your reset link...
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Success state
  if (isSuccess) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6 sm:p-10 transition-all duration-300">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center bg-green-600 rounded-xl mx-auto mb-6 w-16 h-16 shadow-md">
                <CheckCircle2 className="text-white w-8 h-8" />
              </div>
              <h1 className="font-bold text-slate-900 text-2xl sm:text-3xl mb-2">
                Password Reset Successful
              </h1>
              <p className="text-slate-600 text-base mb-4">
                Your password has been successfully updated.
              </p>
              <p className="text-sm text-slate-500">
                Redirecting to login page in a few seconds...
              </p>
            </div>

            <Link to="/login">
              <Button
                className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200"
              >
                Continue to Login
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Invalid token state
  if (!isValidToken) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6 sm:p-10 transition-all duration-300">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center bg-red-600 rounded-xl mx-auto mb-6 w-16 h-16 shadow-md">
                <AlertCircle className="text-white w-8 h-8" />
              </div>
              <h1 className="font-bold text-slate-900 text-2xl sm:text-3xl mb-2">
                Invalid Reset Link
              </h1>
              <p className="text-slate-600 text-base mb-4">
                {errors.general || 'This reset link has expired or is invalid.'}
              </p>
            </div>

            <div className="space-y-4">
              <Link to="/forgot-password">
                <Button
                  className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200"
                >
                  Request New Reset Link
                </Button>
              </Link>
              
              <Link to="/login">
                <Button
                  variant="outline"
                  className="w-full h-12 border-slate-300 text-slate-700 hover:bg-slate-50 transition-all duration-200"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Login
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6 sm:p-10 transition-all duration-300">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center bg-blue-600 rounded-xl mx-auto mb-6 w-16 h-16 shadow-md transform transition-transform hover:scale-105 duration-300">
              <MessageSquare className="text-white w-8 h-8" />
            </div>
            <h1 className="font-bold text-slate-900 text-2xl sm:text-3xl mb-2">
              Reset Your Password
            </h1>
            <p className="text-slate-600 text-base">
              Enter your new password below.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5" autoComplete="on">
            {/* General Error Message */}
            {errors.general && (
              <div className="flex items-center gap-2 p-4 rounded-lg bg-red-50 text-red-600 text-sm mb-4 animate-in fade-in duration-300">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{errors.general}</span>
              </div>
            )}

            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
                <Lock className="w-4 h-4" />
                <span>New Password</span>
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  className={`h-12 pl-3 border-slate-300 focus:border-blue-500 focus:ring-blue-500 pr-12 transition-all duration-200 ${
                    errors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 
                    touchedFields.password && !errors.password ? 'border-green-500 focus:border-green-500 focus:ring-green-500' : ''
                  }`}
                  autoComplete="new-password"
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "password-error" : undefined}
                  disabled={isLoading}
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 hover:text-slate-700 focus:outline-none focus:text-blue-600 transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={0}
                  disabled={isLoading}
                >
                  {showPassword ? 
                    <EyeOff className="w-5 h-5" /> : 
                    <Eye className="w-5 h-5" />
                  }
                </button>
              </div>
              {errors.password && (
                <div id="password-error" className="flex items-center gap-1.5 text-red-600 text-sm mt-1 animate-in fade-in duration-200">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{errors.password}</span>
                </div>
              )}
              <div className="text-xs text-slate-500 mt-1">
                Password must be at least 8 characters with uppercase, lowercase, and number.
              </div>
            </div>

            {/* Confirm Password Field */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
                <Lock className="w-4 h-4" />
                <span>Confirm New Password</span>
              </Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  className={`h-12 pl-3 border-slate-300 focus:border-blue-500 focus:ring-blue-500 pr-12 transition-all duration-200 ${
                    errors.confirmPassword ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 
                    touchedFields.confirmPassword && !errors.confirmPassword ? 'border-green-500 focus:border-green-500 focus:ring-green-500' : ''
                  }`}
                  autoComplete="new-password"
                  aria-invalid={!!errors.confirmPassword}
                  aria-describedby={errors.confirmPassword ? "confirm-password-error" : undefined}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 hover:text-slate-700 focus:outline-none focus:text-blue-600 transition-colors"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                  tabIndex={0}
                  disabled={isLoading}
                >
                  {showConfirmPassword ? 
                    <EyeOff className="w-5 h-5" /> : 
                    <Eye className="w-5 h-5" />
                  }
                </button>
              </div>
              {errors.confirmPassword && (
                <div id="confirm-password-error" className="flex items-center gap-1.5 text-red-600 text-sm mt-1 animate-in fade-in duration-200">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{errors.confirmPassword}</span>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-medium transition-all duration-200 
                focus:ring-4 focus:ring-blue-200 active:translate-y-0.5 disabled:opacity-70 mt-6 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Resetting Password...</span>
                </>
              ) : (
                'Reset Password'
              )}
            </Button>
          </form>
        </div>

        {/* Back to Login Link */}
        <div className="text-center text-sm text-slate-600 mt-8">
          <p className="flex items-center justify-center gap-1">
            <Link 
              to="/login" 
              className="text-blue-600 hover:text-blue-700 hover:underline font-medium transition-all duration-200 focus:outline-none focus:underline flex items-center gap-1"
              tabIndex={0}
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
