
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, User, Settings, LogOut, UserCircle } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useProfile } from '@/hooks/redux/useProfile';
import { useAuth } from '@/hooks/redux/useAuth';

export const TopNavbar: React.FC = () => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const navigate = useNavigate();
  const { profile, profilePictureVersion, displayName, initials, avatarUrl } = useProfile();
  const { logout } = useAuth();

  const handleNavigate = (path: string) => {
    // add log for test
    console.log(`Navigating to ${path}`);
    navigate(path);
    setShowUserDropdown(false);
  };

  const handleLogout = async () => {
    console.log('Logging out user');
    try {
      await logout();
      setShowUserDropdown(false);
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Still navigate to login even if logout API fails
      setShowUserDropdown(false);
      navigate('/login');
    }
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <header className="sticky top-0 bg-white border-b border-slate-200 px-4 lg:px-6 py-4 z-30">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-slate-900">
            ChatFlow
          </h1>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="relative">
            <button
              onClick={() => {
                console.log('Dropdown toggle clicked, current state:', showUserDropdown);
                setShowUserDropdown(!showUserDropdown);
              }}
              className="flex items-center gap-3 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl hover:bg-slate-100 transition-colors"
            >
              <Avatar className="w-8 h-8">
                <AvatarImage 
                  src={avatarUrl || ""} 
                  alt={displayName} 
                />
                <AvatarFallback className="text-xs font-semibold bg-blue-600 text-white">
                  {initials || <User className="w-4 h-4" />}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium text-slate-700">
                {displayName}
              </span>
              <ChevronDown className="w-4 h-4 text-slate-500" />
            </button>

            {showUserDropdown && (
              <>
                <div 
                  className="fixed inset-0 z-40"
                  onClick={() => setShowUserDropdown(false)}
                />
                <div className="absolute top-full right-0 mt-2 w-48 bg-white border border-slate-200 rounded-xl shadow-lg z-50">
                  <div className="p-2">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log('Profile button clicked');
                        handleNavigate('/profile');
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-lg transition-colors"
                    >
                      <UserCircle className="w-4 h-4 text-slate-500" />
                      <span>View Profile</span>
                    </button>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log('Settings button clicked');
                        handleNavigate('/settings');
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-lg transition-colors"
                    >
                      <Settings className="w-4 h-4 text-slate-500" />
                      <span>Settings</span>
                    </button>
                    <hr className="border-slate-200 my-2" />
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleLogout();
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Log out</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
