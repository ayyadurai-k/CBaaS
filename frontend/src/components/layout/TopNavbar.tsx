
import React, { useState } from 'react';
import { ChevronDown, User, Settings, LogOut, UserCircle } from 'lucide-react';

export const TopNavbar: React.FC = () => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  return (
    <>
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
                onClick={() => setShowUserDropdown(!showUserDropdown)}
                className="flex items-center gap-3 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl hover:bg-slate-100 transition-colors"
              >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium text-slate-700">
                  John Doe
                </span>
                <ChevronDown className="w-4 h-4 text-slate-500" />
              </button>

              {showUserDropdown && (
                <div className="absolute top-full right-0 mt-2 w-48 bg-white border border-slate-200 rounded-xl shadow-lg z-50">
                  <div className="p-2">
                    <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-lg transition-colors">
                      <UserCircle className="w-4 h-4 text-slate-500" />
                      <span>View Profile</span>
                    </button>
                    <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-lg transition-colors">
                      <Settings className="w-4 h-4 text-slate-500" />
                      <span>Settings</span>
                    </button>
                    <hr className="border-slate-200 my-2" />
                    <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                      <LogOut className="w-4 h-4" />
                      <span>Log out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {showUserDropdown && (
        <div 
          className="fixed inset-0 z-40"
          onClick={() => setShowUserDropdown(false)}
        />
      )}
    </>
  );
};
