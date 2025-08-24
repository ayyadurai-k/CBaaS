
import React, { useState } from 'react';
import { Key, Plus, Copy, Trash2, Eye, EyeOff, X, AlertTriangle, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';

interface ApiKey {
  id: string;
  name: string;
  key: string;
  maskedKey: string;
  createdDate: string;
  usageQuota: string;
  status: 'active' | 'revoked';
  expirationDate?: string;
  scope: string;
}

const mockApiKeys: ApiKey[] = [
  {
    id: '1',
    name: 'Production Key',
    key: 'sk-1234567890abcdef1234567890abcdef',
    maskedKey: 'sk-••••••••••••••••••••••••••••cdef',
    createdDate: '2024-01-15',
    usageQuota: '8,432 / 10,000',
    status: 'active',
    scope: 'Full Access'
  },
  {
    id: '2',
    name: 'Development Key',
    key: 'sk-abcdef1234567890abcdef1234567890',
    maskedKey: 'sk-••••••••••••••••••••••••••••7890',
    createdDate: '2024-01-10',
    usageQuota: '1,205 / 5,000',
    status: 'active',
    scope: 'Read-only'
  }
];

export const ApiKeysPage: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>(mockApiKeys);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState<{ type: 'revoke' | 'delete', keyId: string, keyName: string } | null>(null);
  const [copiedStates, setCopiedStates] = useState<Set<string>>(new Set());
  
  // Form state for new API key
  const [keyName, setKeyName] = useState('');
  const [usageQuota, setUsageQuota] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [scope, setScope] = useState('full-access');

  const toggleKeyVisibility = (keyId: string) => {
    const newVisibleKeys = new Set(visibleKeys);
    if (newVisibleKeys.has(keyId)) {
      newVisibleKeys.delete(keyId);
    } else {
      newVisibleKeys.add(keyId);
    }
    setVisibleKeys(newVisibleKeys);
  };

  const copyToClipboard = (text: string, keyId: string) => {
    navigator.clipboard.writeText(text);
    
    // Add to copied states
    setCopiedStates(prev => new Set(prev).add(keyId));
    
    // Remove after animation
    setTimeout(() => {
      setCopiedStates(prev => {
        const newSet = new Set(prev);
        newSet.delete(keyId);
        return newSet;
      });
    }, 2000);

    toast({
      title: "Copied to clipboard",
      description: "API key has been copied to your clipboard",
    });
  };

  const handleConfirmAction = () => {
    if (!showConfirmModal) return;

    const { type, keyId } = showConfirmModal;
    
    if (type === 'revoke') {
      setApiKeys(apiKeys.map(key => 
        key.id === keyId ? { ...key, status: 'revoked' as const } : key
      ));
      toast({
        title: "API key revoked",
        description: "The API key has been revoked and is no longer active",
      });
    } else if (type === 'delete') {
      setApiKeys(apiKeys.filter(key => key.id !== keyId));
      toast({
        title: "API key deleted",
        description: "The API key has been permanently deleted",
      });
    }
    
    setShowConfirmModal(null);
  };

  const generateRandomKey = () => {
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = 'sk-';
    for (let i = 0; i < 48; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  const handleGenerateKey = () => {
    if (!keyName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a key name",
        variant: "destructive",
      });
      return;
    }

    const newKey = generateRandomKey();
    const newApiKey: ApiKey = {
      id: Date.now().toString(),
      name: keyName,
      key: newKey,
      maskedKey: newKey.substring(0, 3) + '••••••••••••••••••••••••••••' + newKey.substring(newKey.length - 4),
      createdDate: new Date().toISOString().split('T')[0],
      usageQuota: usageQuota ? `0 / ${usageQuota}` : '0 / ∞',
      status: 'active',
      expirationDate: expirationDate || undefined,
      scope: scope === 'full-access' ? 'Full Access' : scope === 'read-only' ? 'Read-only' : 'Upload-only'
    };

    setApiKeys([newApiKey, ...apiKeys]);
    
    // Reset form
    setKeyName('');
    setUsageQuota('');
    setExpirationDate('');
    setScope('full-access');
    setShowGenerateModal(false);

    toast({
      title: "API key created successfully",
      description: "Your new API key has been generated and is ready to use",
    });
  };

  const resetModal = () => {
    setKeyName('');
    setUsageQuota('');
    setExpirationDate('');
    setScope('full-access');
    setShowGenerateModal(false);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Developer Access</h1>
          <p className="text-slate-600">Manage API keys to integrate your chatbot into applications</p>
        </div>
        <Button 
          onClick={() => setShowGenerateModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium"
        >
          <Plus className="w-5 h-5 mr-2" />
          Generate New Key
        </Button>
      </div>

      {/* API Keys List */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-8">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Name</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">API Key</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Created</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Usage</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Scope</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Status</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {apiKeys.map((apiKey) => (
                <tr key={apiKey.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-4 px-6">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                        <Key className="w-5 h-5 text-blue-600" />
                      </div>
                      <span className="font-medium text-slate-900">{apiKey.name}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center space-x-2">
                      <code className="text-sm font-mono text-slate-600 bg-slate-50 px-2 py-1 rounded">
                        {visibleKeys.has(apiKey.id) ? apiKey.key : apiKey.maskedKey}
                      </code>
                      <button
                        onClick={() => toggleKeyVisibility(apiKey.id)}
                        className="p-1 text-slate-500 hover:text-slate-700 transition-colors"
                      >
                        {visibleKeys.has(apiKey.id) ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                      <div className="relative">
                        <button
                          onClick={() => copyToClipboard(apiKey.key, apiKey.id)}
                          className={`p-1 text-slate-500 hover:text-slate-700 transition-all duration-200 ${
                            copiedStates.has(apiKey.id) ? 'scale-110' : 'scale-100'
                          }`}
                        >
                          {copiedStates.has(apiKey.id) ? (
                            <Check className="w-4 h-4 text-green-600" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                        {copiedStates.has(apiKey.id) && (
                          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-slate-900 text-white text-xs px-2 py-1 rounded animate-fade-in">
                            Copied!
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-slate-600">{apiKey.createdDate}</td>
                  <td className="py-4 px-6 text-slate-600">{apiKey.usageQuota}</td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                      {apiKey.scope}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      apiKey.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {apiKey.status}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center space-x-2">
                      {apiKey.status === 'active' && (
                        <button 
                          onClick={() => setShowConfirmModal({ type: 'revoke', keyId: apiKey.id, keyName: apiKey.name })}
                          className="p-2 text-slate-600 hover:text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors"
                        >
                          <AlertTriangle className="w-4 h-4" />
                        </button>
                      )}
                      <button 
                        onClick={() => setShowConfirmModal({ type: 'delete', keyId: apiKey.id, keyName: apiKey.name })}
                        className="p-2 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Usage Example */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Usage Example</h3>
        <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto relative">
          <pre className="text-sm text-slate-300">
            <code>{`curl -X POST https://api.chatflow.com/v1/chat \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "What is our vacation policy?",
    "conversation_id": "optional-conversation-id"
  }'`}</code>
          </pre>
          <button
            onClick={() => copyToClipboard(`curl -X POST https://api.chatflow.com/v1/chat \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "What is our vacation policy?",
    "conversation_id": "optional-conversation-id"
  }'`, 'example')}
            className={`absolute top-3 right-3 p-2 text-slate-400 hover:text-white transition-all duration-200 ${
              copiedStates.has('example') ? 'scale-110' : 'scale-100'
            }`}
          >
            {copiedStates.has('example') ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Generate API Key Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-slate-900">Generate New API Key</h3>
              <button 
                onClick={resetModal}
                className="text-slate-500 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="key-name" className="text-sm font-medium text-slate-700">
                  Key Name *
                </Label>
                <Input
                  id="key-name"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  placeholder="e.g., Production API, Development Key"
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="usage-quota" className="text-sm font-medium text-slate-700">
                  Usage Quota (Optional)
                </Label>
                <Input
                  id="usage-quota"
                  type="number"
                  value={usageQuota}
                  onChange={(e) => setUsageQuota(e.target.value)}
                  placeholder="e.g., 10000"
                  className="mt-1"
                />
                <p className="text-xs text-slate-500 mt-1">Leave empty for unlimited usage</p>
              </div>

              <div>
                <Label htmlFor="expiration-date" className="text-sm font-medium text-slate-700">
                  Expiration Date (Optional)
                </Label>
                <Input
                  id="expiration-date"
                  type="date"
                  value={expirationDate}
                  onChange={(e) => setExpirationDate(e.target.value)}
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="scope" className="text-sm font-medium text-slate-700">
                  Scope
                </Label>
                <select
                  id="scope"
                  value={scope}
                  onChange={(e) => setScope(e.target.value)}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="full-access">Full Access</option>
                  <option value="read-only">Read-only</option>
                  <option value="upload-only">Upload-only</option>
                </select>
              </div>

              <div className="flex space-x-3 pt-4">
                <Button
                  onClick={resetModal}
                  variant="outline"
                  className="flex-1 rounded-xl"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleGenerateKey}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-xl"
                >
                  Generate Key
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-900">
                  {showConfirmModal.type === 'revoke' ? 'Revoke API Key' : 'Delete API Key'}
                </h3>
                <p className="text-sm text-slate-600">
                  {showConfirmModal.keyName}
                </p>
              </div>
            </div>
            
            <p className="text-slate-600 mb-6">
              {showConfirmModal.type === 'revoke' 
                ? 'This will deactivate the API key. You can reactivate it later if needed.'
                : 'This action cannot be undone. The API key will be permanently deleted.'
              }
            </p>
            
            <div className="flex space-x-3">
              <Button
                onClick={() => setShowConfirmModal(null)}
                variant="outline"
                className="flex-1 rounded-xl"
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmAction}
                className={`flex-1 rounded-xl ${
                  showConfirmModal.type === 'revoke' 
                    ? 'bg-yellow-600 hover:bg-yellow-700' 
                    : 'bg-red-600 hover:bg-red-700'
                } text-white`}
              >
                {showConfirmModal.type === 'revoke' ? 'Revoke' : 'Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
