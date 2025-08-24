
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Settings, Edit, Trash2, FileText } from 'lucide-react';
import { CreateChatbotModal } from '@/components/chatbot/CreateChatbotModal';

const chatbots = [
  {
    id: 1,
    name: 'Customer Support Bot',
    status: 'Active',
    dataSets: ['FAQ Document', 'Product Manual'],
    createdDate: '2024-01-15',
    queries: 1240,
  },
  {
    id: 2,
    name: 'Sales Assistant',
    status: 'Active',
    dataSets: ['Product Catalog', 'Pricing Guide'],
    createdDate: '2024-01-10',
    queries: 856,
  },
  {
    id: 3,
    name: 'Technical Support',
    status: 'Disabled',
    dataSets: ['Technical Documentation'],
    createdDate: '2024-01-05',
    queries: 324,
  },
  {
    id: 4,
    name: 'HR Assistant',
    status: 'Active',
    dataSets: ['Employee Handbook', 'Policies'],
    createdDate: '2024-01-20',
    queries: 198,
  },
];

export const ChatbotsPage: React.FC = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Chatbot Instances</h1>
          <p className="text-slate-600 mt-2">Manage and configure your AI chatbots</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Settings className="w-4 h-4 mr-2" />
          Create New Chatbot
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-slate-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">Total Chatbots</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">4</div>
            <p className="text-xs text-slate-500">3 active, 1 disabled</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">Total Queries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">2,618</div>
            <p className="text-xs text-green-600">↗ +18% this month</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-600">Avg Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">1.2s</div>
            <p className="text-xs text-green-600">↗ 15% faster</p>
          </CardContent>
        </Card>
      </div>

      {/* Chatbots Table */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-slate-900">Your Chatbots</CardTitle>
          <p className="text-sm text-slate-600">Manage your AI assistants and their configurations</p>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Linked Data Sets</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Queries</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {chatbots.map((bot) => (
                <TableRow key={bot.id}>
                  <TableCell className="font-medium">{bot.name}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      bot.status === 'Active' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {bot.status}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {bot.dataSets.map((dataset, index) => (
                        <span key={index} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs">
                          <FileText className="w-3 h-3" />
                          {dataset}
                        </span>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-600">{bot.createdDate}</TableCell>
                  <TableCell className="font-mono">{bot.queries.toLocaleString()}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        Preview
                      </Button>
                      <Button variant="outline" size="sm">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <CreateChatbotModal 
        isOpen={isCreateModalOpen} 
        onClose={() => setIsCreateModalOpen(false)} 
      />
    </div>
  );
};
