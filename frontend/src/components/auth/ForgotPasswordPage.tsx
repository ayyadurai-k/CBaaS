import React, { useState } from 'react';
import { MessageSquare, Mail, AlertCircle, Loader2, CheckCircle2, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Link } from 'react-router-dom';
import { authService } from '@/services/auth/AuthService';
import { getErrorMessage } from '@/apis/configs/axiosUtils';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [touchedFields, setTouchedFields] = useState<{[key: string]: boolean}>({});

  // Validate email format
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Real-time field validation
  const validateField = (name: string, value: string): string => {
    if (name === 'email') {
      if (!value.trim()) return 'Email is required';
      if (!validateEmail(value)) return 'Please enter a valid email address';
    }
    return '';
  };

  // Handle input changes with real-time validation
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setEmail(value);
    
    // Only show errors if the field has been touched
    if (touchedFields[name]) {
      const error = validateField(name, value);
      setErrors(prev => ({ ...prev, [name]: error }));
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
    
    // Mark field as touched
    setTouchedFields({ email: true });
    
    // Validate email
    const emailError = validateField('email', email);
    if (emailError) {
      setErrors({ email: emailError });
      return;
    }

    // Clear any previous errors
    setErrors({});
    setIsLoading(true);

    try {
      const result = await authService.forgotPassword({ email });
      
      if (result.success) {
        setIsSubmitted(true);
      } else {
        // Handle specific error messages
        if (result.message?.toLowerCase().includes('not found') || result.message?.toLowerCase().includes('exist')) {
          setErrors({ general: 'No account found with this email address.' });
        } else if (result.message?.toLowerCase().includes('recently')) {
          setErrors({ general: 'Password reset email was recently sent. Please check your inbox or try again later.' });
        } else {
          setErrors({ general: result.message || 'Failed to send reset email. Please try again.' });
        }
      }
    } catch (error) {
      const errorMessage = getErrorMessage(error, 'Network error. Please check your connection and try again.');
      setErrors({ general: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  // Success state - email sent
  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6 sm:p-10 transition-all duration-300">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center bg-green-600 rounded-xl mx-auto mb-6 w-16 h-16 shadow-md">
                <CheckCircle2 className="text-white w-8 h-8" />
              </div>
              <h1 className="font-bold text-slate-900 text-2xl sm:text-3xl mb-2">
                Check Your Email
              </h1>
              <p className="text-slate-600 text-base mb-4">
                We've sent a password reset link to
              </p>
              <p className="text-blue-600 font-medium text-base mb-6">
                {email}
              </p>
              <div className="text-sm text-slate-600 space-y-2">
                <p>Click the link in the email to reset your password.</p>
                <p>If you don't see it, check your spam folder.</p>
              </div>
            </div>

            <div className="space-y-4">
              <Button
                onClick={() => {
                  setIsSubmitted(false);
                  setEmail('');
                  setTouchedFields({});
                  setErrors({});
                }}
                variant="outline"
                className="w-full h-12 border-slate-300 text-slate-700 hover:bg-slate-50 transition-all duration-200"
              >
                Send Another Email
              </Button>
              
              <Link to="/login">
                <Button
                  variant="default"
                  className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200"
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
              Forgot Password?
            </h1>
            <p className="text-slate-600 text-base">
              Enter your email address and we'll send you a link to reset your password.
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

            {/* Email Field */}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
                <Mail className="w-4 h-4" />
                <span>Email Address</span>
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  className={`h-12 pl-3 border-slate-300 focus:border-blue-500 focus:ring-blue-500 transition-all duration-200 ${
                    errors.email ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 
                    touchedFields.email && !errors.email ? 'border-green-500 focus:border-green-500 focus:ring-green-500' : ''
                  }`}
                  autoComplete="email"
                  spellCheck="false"
                  autoCapitalize="none"
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? "email-error" : undefined}
                  disabled={isLoading}
                  autoFocus
                />
                {touchedFields.email && !errors.email && email && (
                  <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-green-500" />
                )}
              </div>
              {errors.email && (
                <div id="email-error" className="flex items-center gap-1.5 text-red-600 text-sm mt-1 animate-in fade-in duration-200">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{errors.email}</span>
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
                  <span>Sending Reset Link...</span>
                </>
              ) : (
                'Send Reset Link'
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
