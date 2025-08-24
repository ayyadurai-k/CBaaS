
import React, { useState } from 'react';
import { MessageSquare, Eye, EyeOff, AlertCircle, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Link } from 'react-router-dom';

interface FormData {
  fullName: string;
  companyName: string;
  email: string;
  phoneNumber: string;
  password: string;
  confirmPassword: string;
}

interface ValidationErrors {
  [key: string]: string;
}

export const SignupPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    fullName: '',
    companyName: '',
    email: '',
    phoneNumber: '',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isLoading, setIsLoading] = useState(false);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string) => {
    const requirements = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    return requirements;
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }

    // Real-time validation for specific fields
    if (field === 'email' && value) {
      if (!validateEmail(value)) {
        setErrors(prev => ({ ...prev, email: 'Please enter a valid email address' }));
      }
    }

    if (field === 'confirmPassword' && value) {
      if (value !== formData.password) {
        setErrors(prev => ({ ...prev, confirmPassword: 'Passwords do not match' }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setIsLoading(true);

    // Comprehensive validation
    const newErrors: ValidationErrors = {};

    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    }

    if (!formData.companyName.trim()) {
      newErrors.companyName = 'Company name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.phoneNumber.trim()) {
      newErrors.phoneNumber = 'Phone number is required';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else {
      const passwordReqs = validatePassword(formData.password);
      if (!passwordReqs.length || !passwordReqs.uppercase || !passwordReqs.number || !passwordReqs.special) {
        newErrors.password = 'Password does not meet requirements';
      }
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setIsLoading(false);
      return;
    }

    // Simulate signup attempt
    setTimeout(() => {
      console.log('Signup attempt:', formData);
      setIsLoading(false);
      // Add your signup logic here
    }, 1500);
  };

  const passwordRequirements = validatePassword(formData.password);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center" style={{ padding: '48px 24px' }}>
      <div style={{ width: '100%', maxWidth: '480px' }}>
        <div className="bg-white rounded-lg shadow-sm border border-slate-200" style={{ padding: '48px' }}>
          <div className="text-center" style={{ marginBottom: '48px' }}>
            <div 
              className="inline-flex items-center justify-center bg-blue-600 rounded-lg mx-auto"
              style={{ width: '64px', height: '64px', marginBottom: '24px' }}
            >
              <MessageSquare className="text-white" style={{ width: '32px', height: '32px' }} />
            </div>
            <h1 
              className="font-bold text-slate-900"
              style={{ fontSize: '28px', lineHeight: '32px', marginBottom: '8px' }}
            >
              Create Account
            </h1>
            <p 
              className="text-slate-600"
              style={{ fontSize: '16px' }}
            >
              Join ChatFlow and start building
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" autoComplete="off" role="form">
            <div className="space-y-2">
              <Label htmlFor="fullName" className="text-sm font-medium text-slate-700">
                Full Name
              </Label>
              <Input
                id="fullName"
                type="text"
                placeholder="Enter your full name"
                value={formData.fullName}
                onChange={(e) => handleInputChange('fullName', e.target.value)}
                className={`h-12 border-slate-300 focus:border-blue-500 focus:ring-blue-500 ${
                  errors.fullName ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                autoComplete="off"
                data-form-type="other"
                aria-describedby={errors.fullName ? 'fullName-error' : undefined}
                required
              />
              {errors.fullName && (
                <div id="fullName-error" className="flex items-center gap-2 text-red-600 text-sm" role="alert">
                  <AlertCircle style={{ width: '16px', height: '16px' }} />
                  <span>{errors.fullName}</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="companyName" className="text-sm font-medium text-slate-700">
                Company Name
              </Label>
              <Input
                id="companyName"
                type="text"
                placeholder="Enter your company name"
                value={formData.companyName}
                onChange={(e) => handleInputChange('companyName', e.target.value)}
                className={`h-12 border-slate-300 focus:border-blue-500 focus:ring-blue-500 ${
                  errors.companyName ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                autoComplete="off"
                data-form-type="other"
                aria-describedby={errors.companyName ? 'companyName-error' : undefined}
                required
              />
              {errors.companyName && (
                <div id="companyName-error" className="flex items-center gap-2 text-red-600 text-sm" role="alert">
                  <AlertCircle style={{ width: '16px', height: '16px' }} />
                  <span>{errors.companyName}</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-slate-700">
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email address"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className={`h-12 border-slate-300 focus:border-blue-500 focus:ring-blue-500 ${
                  errors.email ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                autoComplete="off"
                data-form-type="other"
                aria-describedby={errors.email ? 'email-error' : undefined}
                required
              />
              {errors.email && (
                <div id="email-error" className="flex items-center gap-2 text-red-600 text-sm" role="alert">
                  <AlertCircle style={{ width: '16px', height: '16px' }} />
                  <span>{errors.email}</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="phoneNumber" className="text-sm font-medium text-slate-700">
                Phone Number
              </Label>
              <Input
                id="phoneNumber"
                type="tel"
                placeholder="Enter your phone number"
                value={formData.phoneNumber}
                onChange={(e) => handleInputChange('phoneNumber', e.target.value)}
                className={`h-12 border-slate-300 focus:border-blue-500 focus:ring-blue-500 ${
                  errors.phoneNumber ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                autoComplete="off"
                data-form-type="other"
                aria-describedby={errors.phoneNumber ? 'phoneNumber-error' : undefined}
                required
              />
              {errors.phoneNumber && (
                <div id="phoneNumber-error" className="flex items-center gap-2 text-red-600 text-sm" role="alert">
                  <AlertCircle style={{ width: '16px', height: '16px' }} />
                  <span>{errors.phoneNumber}</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-slate-700">
                Password
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Create a strong password"
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className={`h-12 border-slate-300 focus:border-blue-500 focus:ring-blue-500 pr-12 ${
                    errors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
                  }`}
                  autoComplete="new-password"
                  data-form-type="other"
                  aria-describedby="password-requirements"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center text-slate-500 hover:text-slate-700"
                  style={{ paddingRight: '12px' }}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? 
                    <EyeOff style={{ width: '20px', height: '20px' }} /> : 
                    <Eye style={{ width: '20px', height: '20px' }} />
                  }
                </button>
              </div>
              
              {formData.password && (
                <div id="password-requirements" style={{ marginTop: '12px' }}>
                  <p className="text-xs text-slate-600" style={{ marginBottom: '8px' }}>Password requirements:</p>
                  <div className="grid grid-cols-2 gap-2">
                    <div className={`flex items-center gap-2 text-xs ${passwordRequirements.length ? 'text-green-600' : 'text-slate-500'}`}>
                      <Check style={{ width: '12px', height: '12px', opacity: passwordRequirements.length ? 1 : 0.3 }} />
                      <span>8+ characters</span>
                    </div>
                    <div className={`flex items-center gap-2 text-xs ${passwordRequirements.uppercase ? 'text-green-600' : 'text-slate-500'}`}>
                      <Check style={{ width: '12px', height: '12px', opacity: passwordRequirements.uppercase ? 1 : 0.3 }} />
                      <span>1 uppercase</span>
                    </div>
                    <div className={`flex items-center gap-2 text-xs ${passwordRequirements.number ? 'text-green-600' : 'text-slate-500'}`}>
                      <Check style={{ width: '12px', height: '12px', opacity: passwordRequirements.number ? 1 : 0.3 }} />
                      <span>1 number</span>
                    </div>
                    <div className={`flex items-center gap-2 text-xs ${passwordRequirements.special ? 'text-green-600' : 'text-slate-500'}`}>
                      <Check style={{ width: '12px', height: '12px', opacity: passwordRequirements.special ? 1 : 0.3 }} />
                      <span>1 special char</span>
                    </div>
                  </div>
                </div>
              )}
              
              {errors.password && (
                <div className="flex items-center gap-2 text-red-600 text-sm" role="alert">
                  <AlertCircle style={{ width: '16px', height: '16px' }} />
                  <span>{errors.password}</span>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-sm font-medium text-slate-700">
                Confirm Password
              </Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm your password"
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className={`h-12 border-slate-300 focus:border-blue-500 focus:ring-blue-500 pr-12 ${
                    errors.confirmPassword ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
                  }`}
                  autoComplete="new-password"
                  data-form-type="other"
                  aria-describedby={errors.confirmPassword ? 'confirmPassword-error' : undefined}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 flex items-center text-slate-500 hover:text-slate-700"
                  style={{ paddingRight: '12px' }}
                  aria-label={showConfirmPassword ? 'Hide password confirmation' : 'Show password confirmation'}
                >
                  {showConfirmPassword ? 
                    <EyeOff style={{ width: '20px', height: '20px' }} /> : 
                    <Eye style={{ width: '20px', height: '20px' }} />
                  }
                </button>
              </div>
              {errors.confirmPassword && (
                <div id="confirmPassword-error" className="flex items-center gap-2 text-red-600 text-sm" role="alert">
                  <AlertCircle style={{ width: '16px', height: '16px' }} />
                  <span>{errors.confirmPassword}</span>
                </div>
              )}
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors disabled:opacity-50"
              style={{ marginTop: '32px' }}
            >
              {isLoading ? 'Creating Account...' : 'Sign Up'}
            </Button>
          </form>
        </div>

        <div className="text-center text-sm text-slate-600" style={{ marginTop: '32px' }}>
          <p>
            Already have an account?{' '}
            <Link 
              to="/login" 
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
