
import React, { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Upload, FileText, Settings, Users, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { getUserProfileThunk } from '@/store/services/userApi';

const statsData = [
  { name: 'Your Chatbot', value: 'Active', icon: MessageSquare, trend: 'positive' },
  { name: 'Uploaded Documents', value: '847', icon: FileText, trend: 'positive' },
  { name: 'API Requests', value: '24.8K', icon: Upload, trend: 'positive' },
  { name: 'User Queries', value: '18.2K', icon: Users, trend: 'positive' },
];

const usageData = [
  { date: '2024-01-01', requests: 1200 },
  { date: '2024-01-02', requests: 1350 },
  { date: '2024-01-03', requests: 1100 },
  { date: '2024-01-04', requests: 1450 },
  { date: '2024-01-05', requests: 1600 },
  { date: '2024-01-06', requests: 1750 },
  { date: '2024-01-07', requests: 1400 },
];

const recentActivity = [
  { action: 'Chatbot updated', details: 'System instructions modified', time: '2 hours ago' },
  { action: 'Document uploaded', details: 'company-handbook.pdf', time: '4 hours ago' },
  { action: 'API key generated', details: 'Production Key #3', time: '1 day ago' },
  { action: 'Team member invited', details: 'sarah@company.com', time: '2 days ago' },
];

const chartConfig = {
  requests: {
    label: 'API Requests',
    color: 'hsl(var(--primary))',
  },
};

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  
  // Get user profile from Redux store
  const { profile, isLoading } = useAppSelector((state) => state.user);
  
  // Fetch user profile on component mount if not already loaded
  useEffect(() => {
    if (!profile) {
      dispatch(getUserProfileThunk());
    }
  }, [dispatch, profile]);
  
  // Get organization name with fallback
  const organizationName = profile?.organization?.name || 'User';
  
  return (
    <div className="space-y-8">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Welcome, {organizationName}
          </h1>
          <p className="text-base text-slate-600">
            Here's what's happening with your ChatFlow platform today.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button  onClick={()=>navigate("/documents")}  variant="outline" className="px-5 py-3">
            <Upload className="w-4 h-4 mr-2" />
            Upload Document
          </Button>
          <Button onClick={()=>navigate("/chatbot")} className="px-5 py-3">
            <Settings className="w-4 h-4 mr-2" />
            Configure Chatbot
          </Button>
        </div>
      </div>

      {/* Stats Cards - Responsive grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsData.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index} className="border-slate-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">
                  {stat.name}
                </CardTitle>
                <Icon className="w-4 h-4 text-slate-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-slate-900">
                  {stat.value}
                </div>
                {stat.name !== 'Your Chatbot' && (
                  <p className="text-xs text-green-600 mt-1">
                    {stat.trend === 'positive' ? '↗' : '↘'} +12% from last month
                  </p>
                )}
                {stat.name === 'Your Chatbot' && (
                  <p className="text-xs text-green-600 mt-1">
                    ↗ Running smoothly
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Charts - Responsive 2-column grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Usage Chart */}
        <Card className="border-slate-200 overflow-hidden">
          <CardHeader>
            <CardTitle className="text-lg text-slate-900">
              Daily API Usage
            </CardTitle>
            <p className="text-sm text-slate-600">
              Last 7 days
            </p>
          </CardHeader>
          <CardContent className="pb-2">
            <ChartContainer config={chartConfig} className="h-[300px]">
              <LineChart data={usageData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 11 }}
                  height={60}
                />
                <YAxis tick={{ fontSize: 11 }} width={40} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                  type="monotone"
                  dataKey="requests"
                  stroke="var(--color-requests)"
                  strokeWidth={2}
                />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg text-slate-900">
              Recent Activity
            </CardTitle>
            <p className="text-sm text-slate-600">
              Latest updates and changes
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div 
                  key={index} 
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-xl"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {activity.action}
                    </p>
                    <p className="text-xs text-slate-600 truncate">
                      {activity.details}
                    </p>
                  </div>
                  <span className="text-xs text-slate-500 ml-4 flex-shrink-0">
                    {activity.time}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
