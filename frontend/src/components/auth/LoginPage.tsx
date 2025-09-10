import React, { useState, useEffect } from 'react';
import { MessageSquare, Eye, EyeOff, AlertCircle, Loader2, CheckCircle2, Mail, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/redux/useAuth';
import { Checkbox } from '@/components/ui/checkbox';

export const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const [loginSuccess, setLoginSuccess] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [touchedFields, setTouchedFields] = useState<{[key: string]: boolean}>({});
  
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading, error } = useAuth();
  
  // Check for return URL from query params
  const from = new URLSearchParams(location.search).get('from') || '/dashboard';

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
    if (name === 'password') {
      if (!value) return 'Password is required';
      if (value.length < 6) return 'Password must be at least 6 characters';
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
    
    // Mark all fields as touched
    setTouchedFields({ email: true, password: true });
    
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

    try {
      // Use Redux login
      const success = await login(formData.email, formData.password);
      
      if (success) {
        // Save remember me preference if selected
        if (rememberMe) {
          localStorage.setItem('rememberedEmail', formData.email);
        } else {
          localStorage.removeItem('rememberedEmail');
        }
        
        // Show success state briefly before redirecting
        setLoginSuccess(true);
        
        // Redirect after a short delay for better UX
        setTimeout(() => {
          navigate(from);
        }, 800);
      } else {
        // Handle login failure - error is managed by Redux
        const errorMessage = error || 'Login failed. Please try again.';
        if (errorMessage.toLowerCase().includes('credentials')) {
          setErrors({ general: 'Invalid email or password. Please try again.' });
        } else if (errorMessage.toLowerCase().includes('many')) {
          setErrors({ general: 'Too many login attempts. Please try again later.' });
        } else {
          setErrors({ general: errorMessage });
        }
      }
    } catch (err) {
      setErrors({ general: 'Network error. Please check your connection and try again.' });
    }
  };
  
  // Load remembered email on component mount
  useEffect(() => {
    const rememberedEmail = localStorage.getItem('rememberedEmail');
    if (rememberedEmail) {
      setFormData(prev => ({ ...prev, email: rememberedEmail }));
      setRememberMe(true);
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6 sm:p-10 transition-all duration-300">
          <div className="text-center mb-8">
            <div 
              className="inline-flex items-center justify-center bg-blue-600 rounded-xl mx-auto mb-6 w-16 h-16 shadow-md transform transition-transform hover:scale-105 duration-300"
            >
              <MessageSquare className="text-white w-8 h-8" />
            </div>
            <h1 
              className="font-bold text-slate-900 text-2xl sm:text-3xl mb-2"
            >
              Welcome Front
            </h1>
            <p 
              className="text-slate-600 text-base"
            >
              Sign in to your ChatFlow account
            </p>
          </div>

          {/* Success Message */}
          {loginSuccess && (
            <div className="flex items-center justify-center gap-2 p-4 rounded-lg bg-green-50 text-green-600 text-sm mb-6 animate-pulse">
              <CheckCircle2 className="w-5 h-5" />
              <span>Login successful! Redirecting...</span>
            </div>
          )}

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
                <span>Email</span>
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="name@company.com"
                  value={formData.email}
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
                  disabled={isLoading || loginSuccess}
                />
                {touchedFields.email && !errors.email && formData.email && (
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

            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
                <Lock className="w-4 h-4" />
                <span>Password</span>
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
                  autoComplete="current-password"
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "password-error" : undefined}
                  disabled={isLoading || loginSuccess}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 hover:text-slate-700 focus:outline-none focus:text-blue-600 transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={0}
                  disabled={isLoading || loginSuccess}
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
            </div>

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between mt-6">
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="remember" 
                  checked={rememberMe} 
                  onCheckedChange={(checked) => setRememberMe(checked === true)}
                  disabled={isLoading || loginSuccess}
                  className="data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                />
                <Label 
                  htmlFor="remember" 
                  className="text-sm text-slate-600 cursor-pointer select-none"
                >
                  Remember me
                </Label>
              </div>
              <Link 
                to="/forgot-password" 
                className="text-sm text-blue-600 hover:text-blue-700 hover:underline font-medium transition-all duration-200 focus:outline-none focus:underline"
                tabIndex={0}
              >
                Forgot password?
              </Link>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading || loginSuccess}
              className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-medium transition-all duration-200 
                focus:ring-4 focus:ring-blue-200 active:translate-y-0.5 disabled:opacity-70 mt-6 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Signing In...</span>
                </>
              ) : loginSuccess ? (
                <>
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Login Successful</span>
                </>
              ) : (
                'Login'
              )}
            </Button>
          </form>
        </div>

        {/* Sign Up Link */}
        <div className="text-center text-sm text-slate-600 mt-8">
          <p className="flex items-center justify-center gap-1">
            Don't have an account?{' '}
            <Link 
              to="/signup" 
              className="text-blue-600 hover:text-blue-700 hover:underline font-medium transition-all duration-200 focus:outline-none focus:underline"
              tabIndex={0}
            >
              Create account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
