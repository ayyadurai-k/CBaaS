import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { BarChart, TrendingUp, FileText, MessageSquare } from 'lucide-react';

const apiUsageData = [
  { date: '2024-01-01', requests: 1200 },
  { date: '2024-01-02', requests: 1350 },
  { date: '2024-01-03', requests: 1100 },
  { date: '2024-01-04', requests: 1450 },
  { date: '2024-01-05', requests: 1600 },
  { date: '2024-01-06', requests: 1750 },
  { date: '2024-01-07', requests: 1400 },
  { date: '2024-01-08', requests: 1900 },
  { date: '2024-01-09', requests: 2100 },
  { date: '2024-01-10', requests: 1800 },
];

const documentUsageData = [
  { name: 'FAQ Document', usage: 35, color: '#3b82f6' },
  { name: 'Product Manual', usage: 25, color: '#10b981' },
  { name: 'Technical Docs', usage: 20, color: '#f59e0b' },
  { name: 'Employee Handbook', usage: 15, color: '#ef4444' },
  { name: 'Other', usage: 5, color: '#8b5cf6' },
];

const frequentQuestions = [
  { question: 'How do I reset my password?', count: 156, category: 'Account' },
  { question: 'What are your pricing plans?', count: 134, category: 'Billing' },
  { question: 'How do I integrate the API?', count: 98, category: 'Technical' },
  { question: 'Can I cancel my subscription?', count: 87, category: 'Billing' },
  { question: 'How do I upload documents?', count: 72, category: 'Technical' },
];

const unansweredQueries = [
  { query: 'What is your refund policy for enterprise customers?', timestamp: '2024-01-10 14:30' },
  { query: 'How do I set up SSO integration?', timestamp: '2024-01-10 13:45' },
  { query: 'Can I white-label the chatbot interface?', timestamp: '2024-01-10 12:20' },
  { query: 'What are the API rate limits for premium plans?', timestamp: '2024-01-10 11:15' },
];

const chartConfig = {
  requests: {
    label: 'API Requests',
    color: 'hsl(var(--primary))',
  },
};

export const AnalyticsPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Chatbot Analytics</h1>
          <p className="text-slate-600 mt-2">Insights into your chatbot performance and user behavior</p>
        </div>
        <div className="flex items-center space-x-3">
          <select className="px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option>Last 30 days</option>
            <option>Last 7 days</option>
            <option>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-slate-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Requests</CardTitle>
            <TrendingUp className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">47,329</div>
            <p className="text-xs text-green-600 mt-1">↗ +23% from last month</p>
          </CardContent>
        </Card>
        
        <Card className="border-slate-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Avg Response Time</CardTitle>
            <BarChart className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">1.2s</div>
            <p className="text-xs text-green-600 mt-1">↗ 15% faster</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Success Rate</CardTitle>
            <MessageSquare className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">94.7%</div>
            <p className="text-xs text-green-600 mt-1">↗ +2.1% improvement</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Token Usage</CardTitle>
            <FileText className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">2.1M</div>
            <p className="text-xs text-slate-600 mt-1">~$43.20 estimated cost</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* API Usage Chart */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-slate-900">API Request Volume</CardTitle>
            <p className="text-sm text-slate-600">Daily requests over the last 10 days</p>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={apiUsageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Line
                    type="monotone"
                    dataKey="requests"
                    stroke="var(--color-requests)"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Document Usage */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-slate-900">Document Usage Distribution</CardTitle>
            <p className="text-sm text-slate-600">Which documents are referenced most</p>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={documentUsageData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="usage"
                  >
                    {documentUsageData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <ChartTooltip content={<ChartTooltipContent />} />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
            <div className="mt-4 space-y-2">
              {documentUsageData.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-sm">{item.name}</span>
                  </div>
                  <span className="text-sm font-medium">{item.usage}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Frequent Questions */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-slate-900">Most Frequently Asked Questions</CardTitle>
            <p className="text-sm text-slate-600">Top user queries this month</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {frequentQuestions.map((item, index) => (
                <div key={index} className="flex items-start justify-between p-3 bg-slate-50 rounded-xl">
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">{item.question}</p>
                    <p className="text-sm text-slate-600">{item.category}</p>
                  </div>
                  <span className="text-sm font-mono text-slate-500">{item.count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Unanswered Queries */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-slate-900">Queries with No Matching Data</CardTitle>
            <p className="text-sm text-slate-600">Questions that need attention</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {unansweredQueries.map((item, index) => (
                <div key={index} className="p-3 bg-orange-50 border border-orange-200 rounded-xl">
                  <p className="font-medium text-slate-900">{item.query}</p>
                  <p className="text-sm text-slate-600 mt-1">{item.timestamp}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
