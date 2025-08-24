
import React, { useState } from 'react';
import { MessageSquare, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Link } from 'react-router-dom';

export const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setIsLoading(true);

    // Basic validation
    const newErrors: {[key: string]: string} = {};
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }
    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setIsLoading(false);
      return;
    }

    // Simulate login attempt
    setTimeout(() => {
      console.log('Login attempt:', formData);
      setIsLoading(false);
      // Add your login logic here
    }, 1000);
  };

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
              Welcome Back
            </h1>
            <p 
              className="text-slate-600"
              style={{ fontSize: '16px' }}
            >
              Sign in to your ChatFlow account
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" autoComplete="off">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium text-slate-700">
                Username
              </Label>
              <Input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className={`h-12 border-slate-300 focus:border-blue-500 focus:ring-blue-500 ${
                  errors.username ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                autoComplete="off"
                data-form-type="other"
                required
              />
              {errors.username && (
                <div className="flex items-center gap-2 text-red-600 text-sm">
                  <AlertCircle style={{ width: '16px', height: '16px' }} />
                  <span>{errors.username}</span>
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
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className={`h-12 border-slate-300 focus:border-blue-500 focus:ring-blue-500 pr-12 ${
                    errors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
                  }`}
                  autoComplete="new-password"
                  data-form-type="other"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center text-slate-500 hover:text-slate-700"
                  style={{ paddingRight: '12px' }}
                >
                  {showPassword ? 
                    <EyeOff style={{ width: '20px', height: '20px' }} /> : 
                    <Eye style={{ width: '20px', height: '20px' }} />
                  }
                </button>
              </div>
              {errors.password && (
                <div className="flex items-center gap-2 text-red-600 text-sm">
                  <AlertCircle style={{ width: '16px', height: '16px' }} />
                  <span>{errors.password}</span>
                </div>
              )}
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors disabled:opacity-50"
              style={{ marginTop: '32px' }}
            >
              {isLoading ? 'Signing In...' : 'Login'}
            </Button>
          </form>

          <div className="text-center" style={{ marginTop: '32px' }}>
            <Link 
              to="/forgot-password" 
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Forgot password?
            </Link>
          </div>
        </div>

        <div className="text-center text-sm text-slate-600" style={{ marginTop: '32px' }}>
          <p>
            Don't have an account?{' '}
            <Link 
              to="/signup" 
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Create account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
