import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Copy, Settings, Upload, FileText } from 'lucide-react';

const embedScript = `<iframe
  src="https://chatflow.lovable.app/embed/your-bot-id"
  width="400"
  height="600"
  frameborder="0">
</iframe>`;

const jsSnippet = `<script>
  (function() {
    var chatbot = document.createElement('script');
    chatbot.src = 'https://chatflow.lovable.app/widget.js';
    chatbot.setAttribute('data-bot-id', 'your-bot-id');
    document.head.appendChild(chatbot);
  })();
</script>`;

const webhooks = [
  {
    id: 1,
    name: 'Customer Queries',
    url: 'https://api.yoursite.com/webhooks/queries',
    events: ['query.received', 'query.answered'],
    status: 'Active',
  },
  {
    id: 2,
    name: 'Usage Analytics',
    url: 'https://analytics.yoursite.com/chatbot',
    events: ['usage.daily'],
    status: 'Disabled',
  },
];

export const IntegrationsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('embed');
  const [webhookForm, setWebhookForm] = useState({
    name: '',
    url: '',
    secret: '',
    events: [],
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Integrations & Embeds</h1>
          <p className="text-slate-600 mt-2">Connect your chatbot to external services and platforms</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'embed', label: 'Embed Scripts' },
            { id: 'platforms', label: 'Platforms' },
            { id: 'webhooks', label: 'Webhooks' },
            { id: 'api', label: 'API Explorer' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Embed Scripts Tab */}
      {activeTab === 'embed' && (
        <div className="space-y-6">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Iframe Embed</CardTitle>
              <p className="text-sm text-slate-600">Embed the chatbot directly into your website</p>
            </CardHeader>
            <CardContent>
              <div className="bg-slate-50 p-4 rounded-xl">
                <pre className="text-sm text-slate-700 overflow-x-auto">{embedScript}</pre>
              </div>
              <Button className="mt-4" onClick={() => copyToClipboard(embedScript)}>
                <Copy className="w-4 h-4 mr-2" />
                Copy Embed Code
              </Button>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">JavaScript Widget</CardTitle>
              <p className="text-sm text-slate-600">Add a floating chat widget to your site</p>
            </CardHeader>
            <CardContent>
              <div className="bg-slate-50 p-4 rounded-xl">
                <pre className="text-sm text-slate-700 overflow-x-auto">{jsSnippet}</pre>
              </div>
              <Button className="mt-4" onClick={() => copyToClipboard(jsSnippet)}>
                <Copy className="w-4 h-4 mr-2" />
                Copy Widget Code
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Platforms Tab */}
      {activeTab === 'platforms' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">S</span>
                </div>
                <span>Slack Integration</span>
              </CardTitle>
              <p className="text-sm text-slate-600">Connect your chatbot to Slack workspaces</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-sm text-slate-600">
                  Status: <span className="text-red-600 font-medium">Not Connected</span>
                </div>
                <Button>
                  <Settings className="w-4 h-4 mr-2" />
                  Install Slack App
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">T</span>
                </div>
                <span>Microsoft Teams</span>
              </CardTitle>
              <p className="text-sm text-slate-600">Deploy your chatbot to Teams channels</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-sm text-slate-600">
                  Status: <span className="text-red-600 font-medium">Not Connected</span>
                </div>
                <Button>
                  <Settings className="w-4 h-4 mr-2" />
                  Install Teams App
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Webhooks Tab */}
      {activeTab === 'webhooks' && (
        <div className="space-y-6">
          {/* Webhook Configuration Form */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Configure New Webhook</CardTitle>
              <p className="text-sm text-slate-600">Receive real-time notifications about chatbot events</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Webhook Name
                  </label>
                  <input
                    type="text"
                    value={webhookForm.name}
                    onChange={(e) => setWebhookForm({...webhookForm, name: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Customer Queries"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Webhook URL
                  </label>
                  <input
                    type="url"
                    value={webhookForm.url}
                    onChange={(e) => setWebhookForm({...webhookForm, url: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="https://your-site.com/webhook"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Secret Key
                  </label>
                  <input
                    type="password"
                    value={webhookForm.secret}
                    onChange={(e) => setWebhookForm({...webhookForm, secret: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter secret key"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Event Types
                  </label>
                  <select className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option>query.received</option>
                    <option>query.answered</option>
                    <option>usage.daily</option>
                    <option>error.occurred</option>
                  </select>
                </div>
              </div>
              <Button className="mt-6">
                Create Webhook
              </Button>
            </CardContent>
          </Card>

          {/* Existing Webhooks */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Configured Webhooks</CardTitle>
              <p className="text-sm text-slate-600">Manage your existing webhook configurations</p>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>URL</TableHead>
                    <TableHead>Events</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {webhooks.map((webhook) => (
                    <TableRow key={webhook.id}>
                      <TableCell className="font-medium">{webhook.name}</TableCell>
                      <TableCell className="font-mono text-sm">{webhook.url}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {webhook.events.map((event, index) => (
                            <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs">
                              {event}
                            </span>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          webhook.status === 'Active' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {webhook.status}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Button variant="outline" size="sm">
                            Edit
                          </Button>
                          <Button variant="outline" size="sm">
                            Test
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}

      {/* API Explorer Tab */}
      {activeTab === 'api' && (
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-slate-900">API Explorer</CardTitle>
            <p className="text-sm text-slate-600">Test API endpoints and view sample requests</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Sample cURL Request</h3>
                <div className="bg-slate-900 text-slate-100 p-4 rounded-xl overflow-x-auto">
                  <pre className="text-sm">{`curl -X POST https://api.chatflow.com/v1/chat \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Hello, can you help me?",
    "bot_id": "your-bot-id",
    "user_id": "user-123"
  }'`}</pre>
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Response Format</h3>
                <div className="bg-slate-50 p-4 rounded-xl">
                  <pre className="text-sm text-slate-700">{`{
  "response": "Hello! I'd be happy to help you.",
  "bot_id": "your-bot-id",
  "timestamp": "2024-01-10T15:30:00Z",
  "tokens_used": 15
}`}</pre>
                </div>
              </div>

              <Button>
                <FileText className="w-4 h-4 mr-2" />
                View Full API Documentation
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
