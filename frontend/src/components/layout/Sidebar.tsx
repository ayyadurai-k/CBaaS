
import React from 'react';
import { Home, FileText, Settings, Key, Users, BarChart, List, CreditCard } from 'lucide-react';
import { useLocation, Link } from 'react-router-dom';

const menuItems = [
  // { icon: Home, label: 'Dashboard', path: '/dashboard' },
  { icon: FileText, label: 'Documents', path: '/documents' },
  { icon: Settings, label: 'Your Chatbot', path: '/chatbot' },
  // { icon: BarChart, label: 'Analytics', path: '/analytics' },
  // { icon: List, label: 'Documentation', path: '/documentation' },
  { icon: Key, label: 'API Keys', path: '/api-keys' },
  // { icon: Users, label: 'Team', path: '/team' },
  // { icon: CreditCard, label: 'Billing', path: '/billing' },
  { icon: Settings, label: 'Settings', path: '/settings' },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <div className="sticky top-0 h-screen w-64 bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
      <div className="border-b border-slate-200 p-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Settings className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-semibold text-slate-900">
            ChatFlow
          </span>
        </div>
      </div>
      
      <nav className="flex-1 overflow-y-auto p-4">
        <div className="flex flex-col gap-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-decoration-none ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-sm font-medium">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
};
