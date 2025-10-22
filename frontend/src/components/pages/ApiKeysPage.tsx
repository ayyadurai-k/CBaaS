import React, { useState, useEffect } from 'react';
import { Key, Plus, Copy, Trash2, X, AlertTriangle, Check, Loader2, Edit2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';
import { APIKeysAPI, CreateAPIKeyPayload, UpdateAPIKeyPayload, APIKeyScope } from '@/apis/ApiKeysAPI';
import { TablePagination, PaginationData } from '@/components/ui/table-pagination';
import { getErrorMessage } from '@/apis/configs/axiosUtils';

interface ApiKey {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
  expires_at?: string;
  usage_count: number;
  quota?: number;
  status: 'active' | 'revoked' | 'expired';
  scope: APIKeyScope;
  allowed_ips: string[];
  rate_limit_per_minute?: number;
  metadata: Record<string, any>;
  revoked_reason: string;
}

interface NewApiKeyModalData {
  show: boolean;
  createdKey?: string; // The actual API key (only shown once)
}

export const ApiKeysPage: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [newKeyModal, setNewKeyModal] = useState<NewApiKeyModalData>({ show: false });
  const [showConfirmModal, setShowConfirmModal] = useState<{ type: 'revoke' | 'delete', keyId: string, keyName: string } | null>(null);
  const [copiedStates, setCopiedStates] = useState<Set<string>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [paginationData, setPaginationData] = useState<PaginationData>({
    count: 0,
    next: null,
    previous: null,
    results: [],
  });
  
  // Edit state
  const [editingKey, setEditingKey] = useState<ApiKey | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  
  // Form state for new API key
  const [keyName, setKeyName] = useState('');
  const [usageQuota, setUsageQuota] = useState('');
  const [scope, setScope] = useState<APIKeyScope>('full-access');
  const [expiresAt, setExpiresAt] = useState('');
  const [allowedIps, setAllowedIps] = useState<string>('');
  const [rateLimit, setRateLimit] = useState('');
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);

  // Load API keys from backend
  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async (page: number = 1) => {
    try {
      setLoading(true);
      const response = await APIKeysAPI.getAll({ page });
      
      const responseData = response.data;
      
      if (responseData && typeof responseData === 'object' && 'results' in responseData) {
        // Paginated response
        setApiKeys(responseData.results);
        setPaginationData(responseData);
        setCurrentPage(page);
      } else if (Array.isArray(responseData)) {
        // Direct array response (fallback)
        setApiKeys(responseData);
        setPaginationData({
          count: responseData.length,
          next: null,
          previous: null,
          results: responseData,
        });
      }
    } catch (error) {
      console.error('Failed to load API keys:', error);
      const errorMessage = getErrorMessage(error, 'Failed to load API keys. Please try again.');
      setApiKeys([]);
      setPaginationData({
        count: 0,
        next: null,
        previous: null,
        results: [],
      });
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };



  const copyToClipboard = (text: string, itemId: string) => {
    navigator.clipboard.writeText(text);
    
    // Add to copied states
    setCopiedStates(prev => new Set(prev).add(itemId));
    
    // Remove after animation
    setTimeout(() => {
      setCopiedStates(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }, 2000);

    toast({
      title: "Copied to clipboard",
      description: "Content has been copied to your clipboard",
    });
  };

  const handleConfirmAction = async () => {
    if (!showConfirmModal) return;

    const { type, keyId, keyName } = showConfirmModal;
    
    try {
      setIsSubmitting(true);
      
      if (type === 'revoke') {
        await APIKeysAPI.revoke(keyId);
        toast({
          title: "API key revoked",
          description: `${keyName} has been revoked and is no longer active`,
        });
      } else if (type === 'delete') {
        await APIKeysAPI.remove(keyId);
        toast({
          title: "API key deleted",
          description: `${keyName} has been permanently deleted`,
        });
      }
      
      // If we deleted the last item on current page, go to previous page
      if (type === 'delete' && apiKeys.length === 1 && currentPage > 1) {
        await loadApiKeys(currentPage - 1);
      } else {
        await loadApiKeys(currentPage);
      }
    } catch (error) {
      console.error(`Failed to ${type} API key:`, error);
      const errorMessage = getErrorMessage(error, `Failed to ${type} API key. Please try again.`);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
      setShowConfirmModal(null);
    }
  };



  const handleGenerateKey = async () => {
    if (!keyName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a key name",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSubmitting(true);
      
      const payload: CreateAPIKeyPayload = {
        name: keyName.trim(),
        scope,
        ...(usageQuota && { quota: parseInt(usageQuota) }),
        ...(expiresAt && { expires_at: new Date(expiresAt).toISOString() }),
        ...(allowedIps && { allowed_ips: allowedIps.split(',').map(ip => ip.trim()).filter(Boolean) }),
        ...(rateLimit && { rate_limit_per_minute: parseInt(rateLimit) })
      };
      
      const response = await APIKeysAPI.create(payload);
      const newApiKey = response.data;
      
      // Show the created key in a modal (only time it's visible)
      if (newApiKey.api_key) {
        setNewKeyModal({ 
          show: true, 
          createdKey: newApiKey.api_key 
        });
      }
      
      // Reset form and close modal
      resetModal();
      
      // Go to first page to see the new key
      await loadApiKeys(1);
      
      toast({
        title: "API key created successfully",
        description: "Your new API key has been generated. Make sure to copy it now!",
      });
    } catch (error: any) {
      console.error('Failed to create API key:', error);
      const errorMessage = getErrorMessage(error, 'Failed to create API key. Please try again.');
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetModal = () => {
    setKeyName('');
    setUsageQuota('');
    setScope('full-access');
    setExpiresAt('');
    setAllowedIps('');
    setRateLimit('');
    setShowAdvancedOptions(false);
    setShowGenerateModal(false);
  };

  const handleEditStart = (key: ApiKey) => {
    setEditingKey(key);
    setKeyName(key.name);
    setUsageQuota(key.quota?.toString() || '');
    setScope(key.scope);
    setExpiresAt(key.expires_at ? key.expires_at.split('T')[0] : '');
    setAllowedIps(key.allowed_ips.join(', '));
    setRateLimit(key.rate_limit_per_minute?.toString() || '');
    setShowAdvancedOptions(true);
    setShowEditModal(true);
  };

  const handleEditSave = async () => {
    if (!editingKey) return;
    
    if (!keyName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a key name",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSubmitting(true);
      
      const payload: UpdateAPIKeyPayload = {
        name: keyName.trim(),
        scope,
        ...(usageQuota && { quota: parseInt(usageQuota) }),
        ...(expiresAt && { expires_at: new Date(expiresAt).toISOString() }),
        allowed_ips: allowedIps ? allowedIps.split(',').map(ip => ip.trim()).filter(Boolean) : [],
        ...(rateLimit && { rate_limit_per_minute: parseInt(rateLimit) })
      };
      
      await APIKeysAPI.update(editingKey.id, payload);
      
      // Reset form and close modal
      handleEditCancel();
      
      // Reload to see updated data
      await loadApiKeys(currentPage);
      
      toast({
        title: "API key updated",
        description: "The API key has been updated successfully",
      });
    } catch (error: any) {
      console.error('Failed to update API key:', error);
      const errorMessage = getErrorMessage(error, 'Failed to update API key. Please try again.');
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditCancel = () => {
    setEditingKey(null);
    setShowEditModal(false);
    resetModal();
  };

  const getScopeDisplay = (scope: APIKeyScope): string => {
    switch (scope) {
      case 'full-access': return 'Full Access';
      case 'read-only': return 'Read-only';
      case 'upload-only': return 'Upload-only';
      default: return scope;
    }
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  const formatDateTime = (dateString: string | null): string => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getRelativeTime = (dateString: string | null): string => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 30) return `${diffDays}d ago`;
    return formatDate(dateString);
  };

  const isExpiringSoon = (expiresAt: string | null): boolean => {
    if (!expiresAt) return false;
    const expiry = new Date(expiresAt);
    const now = new Date();
    const daysUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    return daysUntilExpiry > 0 && daysUntilExpiry <= 7; // Expires within 7 days
  };

  const formatUsage = (usageCount: number, quota?: number): string => {
    if (quota) {
      return `${usageCount.toLocaleString()} / ${quota.toLocaleString()}`;
    }
    return `${usageCount.toLocaleString()} / ∞`;
  };

  const handlePageChange = (newPage: number) => {
    loadApiKeys(newPage);
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
        <div className="overflow-x-auto overflow-y-auto" style={{ height: '400px' }}>
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200 sticky top-0 z-10">
              <tr>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Name</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Last Used</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Usage</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Scope</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Status</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Expires</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center">
                    <div className="flex items-center justify-center space-x-2 text-slate-500">
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Loading API keys...</span>
                    </div>
                  </td>
                </tr>
              ) : apiKeys.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    <div className="flex flex-col items-center space-y-2">
                      <Key className="w-8 h-8 text-slate-300" />
                      <p>No API keys found</p>
                      <p className="text-sm">Create your first API key to get started</p>
                    </div>
                  </td>
                </tr>
              ) : (
                apiKeys.map((apiKey) => (
                  <tr key={apiKey.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-6">
                      <div className="flex flex-col space-y-1">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                            <Key className="w-5 h-5 text-blue-600" />
                          </div>
                          <span className="font-medium text-slate-900">{apiKey.name}</span>
                        </div>
                        {apiKey.allowed_ips && apiKey.allowed_ips.length > 0 && (
                          <div className="ml-13 text-xs text-slate-500">
                            🔒 IP Restricted ({apiKey.allowed_ips.length} {apiKey.allowed_ips.length === 1 ? 'IP' : 'IPs'})
                          </div>
                        )}
                        {apiKey.rate_limit_per_minute && (
                          <div className="ml-13 text-xs text-slate-500">
                            ⚡ {apiKey.rate_limit_per_minute} req/min
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <div className="text-slate-600">{getRelativeTime(apiKey.last_used_at)}</div>
                      {apiKey.last_used_at && (
                        <div className="text-xs text-slate-400">{formatDateTime(apiKey.last_used_at)}</div>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <div className="text-slate-600">{formatUsage(apiKey.usage_count, apiKey.quota)}</div>
                      {apiKey.quota && (
                        <div className="w-full bg-slate-100 rounded-full h-1.5 mt-1">
                          <div 
                            className={`h-1.5 rounded-full ${
                              (apiKey.usage_count / apiKey.quota) > 0.9 
                                ? 'bg-red-500' 
                                : (apiKey.usage_count / apiKey.quota) > 0.7 
                                  ? 'bg-yellow-500' 
                                  : 'bg-green-500'
                            }`}
                            style={{ width: `${Math.min((apiKey.usage_count / apiKey.quota) * 100, 100)}%` }}
                          />
                        </div>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                        {getScopeDisplay(apiKey.scope)}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        apiKey.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : apiKey.status === 'expired'
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-red-100 text-red-800'
                      }`}>
                        {apiKey.status}
                      </span>
                      {apiKey.status === 'revoked' && apiKey.revoked_reason && (
                        <div className="text-xs text-slate-500 mt-1">
                          {apiKey.revoked_reason}
                        </div>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      {apiKey.expires_at ? (
                        <div className="flex flex-col">
                          <span className={`text-sm ${
                            isExpiringSoon(apiKey.expires_at) 
                              ? 'text-orange-600 font-medium' 
                              : 'text-slate-600'
                          }`}>
                            {formatDate(apiKey.expires_at)}
                          </span>
                          {isExpiringSoon(apiKey.expires_at) && (
                            <span className="text-xs text-orange-600">⚠️ Expiring soon</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-400 text-sm">Never</span>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center space-x-2">
                        {apiKey.status === 'active' && (
                          <>
                            <button 
                              onClick={() => handleEditStart(apiKey)}
                              className="p-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                              disabled={isSubmitting}
                              title="Edit API key"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button 
                              onClick={() => setShowConfirmModal({ type: 'revoke', keyId: apiKey.id, keyName: apiKey.name })}
                              className="p-2 text-slate-600 hover:text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors"
                              disabled={isSubmitting}
                              title="Revoke API key"
                            >
                              <AlertTriangle className="w-4 h-4" />
                            </button>
                          </>
                        )}
                        <button 
                          onClick={() => setShowConfirmModal({ type: 'delete', keyId: apiKey.id, keyName: apiKey.name })}
                          className="p-2 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          disabled={isSubmitting}
                          title="Delete API key"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <TablePagination
          paginationData={paginationData}
          currentPage={currentPage}
          onPageChange={handlePageChange}
          isLoading={loading}
        />
      </div>

      {/* Usage Example */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Usage Example</h3>
        <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto relative">
          <pre className="text-sm text-slate-300">
            <code>{`curl -X POST https://api.yourdomain.com/api/chat/completions \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -H "Idempotency-Key: unique-request-id" \\
  -d '{
    "messages": [
      {"role": "user", "content": "What is our vacation policy?"}
    ],
    "max_tokens": 512,
    "temperature": 0.2
  }'`}</code>
          </pre>
          <button
            onClick={() => copyToClipboard(`curl -X POST https://api.yourdomain.com/api/chat/completions \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -H "Idempotency-Key: unique-request-id" \\
  -d '{
    "messages": [
      {"role": "user", "content": "What is our vacation policy?"}
    ],
    "max_tokens": 512,
    "temperature": 0.2
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4 my-8 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between mb-6 flex-shrink-0">
              <h3 className="text-xl font-semibold text-slate-900">Generate New API Key</h3>
              <button 
                onClick={resetModal}
                className="text-slate-500 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 overflow-y-auto flex-1 pr-2 -mr-2">
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
                <Label htmlFor="scope" className="text-sm font-medium text-slate-700">
                  Scope
                </Label>
                <select
                  id="scope"
                  value={scope}
                  onChange={(e) => setScope(e.target.value as APIKeyScope)}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="full-access">Full Access</option>
                  <option value="read-only">Read-only</option>
                  <option value="upload-only">Upload-only</option>
                </select>
              </div>

              {/* Advanced Options Toggle */}
              <button
                type="button"
                onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                <span>{showAdvancedOptions ? '− Hide' : '+ Show'} Advanced Options</span>
              </button>

              {/* Advanced Options */}
              {showAdvancedOptions && (
                <div className="space-y-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <div>
                    <Label htmlFor="expires-at" className="text-sm font-medium text-slate-700">
                      Expiration Date (Optional)
                    </Label>
                    <Input
                      id="expires-at"
                      type="datetime-local"
                      value={expiresAt}
                      onChange={(e) => setExpiresAt(e.target.value)}
                      min={new Date().toISOString().slice(0, 16)}
                      className="mt-1"
                    />
                    <p className="text-xs text-slate-500 mt-1">Key will automatically expire after this date</p>
                  </div>

                  <div>
                    <Label htmlFor="allowed-ips" className="text-sm font-medium text-slate-700">
                      Allowed IP Addresses (Optional)
                    </Label>
                    <Input
                      id="allowed-ips"
                      value={allowedIps}
                      onChange={(e) => setAllowedIps(e.target.value)}
                      placeholder="e.g., 203.0.113.0, 198.51.100.0"
                      className="mt-1"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Comma-separated list of IPs. Leave empty to allow all IPs
                    </p>
                  </div>

                  <div>
                    <Label htmlFor="rate-limit" className="text-sm font-medium text-slate-700">
                      Rate Limit (Optional)
                    </Label>
                    <Input
                      id="rate-limit"
                      type="number"
                      value={rateLimit}
                      onChange={(e) => setRateLimit(e.target.value)}
                      placeholder="e.g., 60"
                      className="mt-1"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Requests per minute. Leave empty to use default rate limit
                    </p>
                  </div>
                </div>
              )}

              <div className="flex space-x-3 pt-4 flex-shrink-0">
                <Button
                  onClick={resetModal}
                  variant="outline"
                  className="flex-1 rounded-xl"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleGenerateKey}
                  disabled={isSubmitting}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-xl disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Generate Key'
                  )}
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
                disabled={isSubmitting}
                className={`flex-1 rounded-xl ${
                  showConfirmModal.type === 'revoke' 
                    ? 'bg-yellow-600 hover:bg-yellow-700' 
                    : 'bg-red-600 hover:bg-red-700'
                } text-white disabled:opacity-50`}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {showConfirmModal.type === 'revoke' ? 'Revoking...' : 'Deleting...'}
                  </>
                ) : (
                  showConfirmModal.type === 'revoke' ? 'Revoke' : 'Delete'
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* New API Key Display Modal - Shows the key only once */}
      {newKeyModal.show && newKeyModal.createdKey && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-lg w-full mx-4 max-h-[90vh] flex flex-col">
            <div className="flex items-center space-x-3 mb-6 flex-shrink-0">
              <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center">
                <Check className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900">API Key Created!</h3>
                <p className="text-sm text-slate-600">Copy your key now - it won't be shown again</p>
              </div>
            </div>

            <div className="overflow-y-auto flex-1">
              <Label className="text-sm font-medium text-slate-700 mb-2 block">
                Your API Key
              </Label>
              <div className="flex items-center space-x-2 p-3 bg-slate-50 rounded-xl border">
                <code className="flex-1 text-sm font-mono text-slate-900 break-all">
                  {newKeyModal.createdKey}
                </code>
                <div className="relative">
                  <button
                    onClick={() => copyToClipboard(newKeyModal.createdKey!, 'new-key')}
                    className={`p-2 text-slate-500 hover:text-slate-700 transition-all duration-200 ${
                      copiedStates.has('new-key') ? 'scale-110' : 'scale-100'
                    }`}
                  >
                    {copiedStates.has('new-key') ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                  {copiedStates.has('new-key') && (
                    <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-slate-900 text-white text-xs px-2 py-1 rounded animate-fade-in">
                      Copied!
                    </div>
                  )}
                </div>
              </div>
            

            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-yellow-800">
                  <p className="font-medium mb-1">Important Security Notice</p>
                  <p>This is the only time you'll see this API key. Make sure to copy and store it securely.</p>
                </div>
              </div>
            </div>
            </div>

            <Button
              onClick={() => setNewKeyModal({ show: false })}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-xl flex-shrink-0"
            >
              I've Copied My Key
            </Button>
          </div>
        </div>
      )}

      {/* Edit API Key Modal */}
      {showEditModal && editingKey && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4 my-8 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between mb-6 flex-shrink-0">
              <h3 className="text-xl font-semibold text-slate-900">Edit API Key</h3>
              <button 
                onClick={handleEditCancel}
                className="text-slate-500 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 overflow-y-auto flex-1 pr-2 -mr-2">
              <div>
                <Label htmlFor="edit-key-name" className="text-sm font-medium text-slate-700">
                  Key Name *
                </Label>
                <Input
                  id="edit-key-name"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  placeholder="e.g., Production API, Development Key"
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="edit-usage-quota" className="text-sm font-medium text-slate-700">
                  Usage Quota
                </Label>
                <Input
                  id="edit-usage-quota"
                  type="number"
                  value={usageQuota}
                  onChange={(e) => setUsageQuota(e.target.value)}
                  placeholder="e.g., 10000"
                  className="mt-1"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Current usage: {editingKey.usage_count}. Cannot set below current usage.
                </p>
              </div>

              <div>
                <Label htmlFor="edit-scope" className="text-sm font-medium text-slate-700">
                  Scope
                </Label>
                <select
                  id="edit-scope"
                  value={scope}
                  onChange={(e) => setScope(e.target.value as APIKeyScope)}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="full-access">Full Access</option>
                  <option value="read-only">Read-only</option>
                  <option value="upload-only">Upload-only</option>
                </select>
                <p className="text-xs text-orange-600 mt-1">
                  ⚠️ Security: Can only downgrade scope (e.g., Full → Read-only)
                </p>
              </div>

              {/* Advanced Options */}
              <div className="border-t border-slate-200 pt-4">
                <button
                  onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                  className="flex items-center justify-between w-full text-sm font-medium text-slate-700 hover:text-blue-600"
                >
                  <span>Advanced Options</span>
                  <span className="text-slate-400">{showAdvancedOptions ? '▼' : '▶'}</span>
                </button>

                {showAdvancedOptions && (
                  <div className="mt-4 space-y-4">
                    <div>
                      <Label htmlFor="edit-expires-at" className="text-sm font-medium text-slate-700">
                        Expiration Date
                      </Label>
                      <Input
                        id="edit-expires-at"
                        type="date"
                        value={expiresAt}
                        onChange={(e) => setExpiresAt(e.target.value)}
                        className="mt-1"
                      />
                      <p className="text-xs text-slate-500 mt-1">Leave empty for no expiration</p>
                    </div>

                    <div>
                      <Label htmlFor="edit-allowed-ips" className="text-sm font-medium text-slate-700">
                        Allowed IP Addresses
                      </Label>
                      <Input
                        id="edit-allowed-ips"
                        value={allowedIps}
                        onChange={(e) => setAllowedIps(e.target.value)}
                        placeholder="e.g., 192.168.1.1, 10.0.0.0/24"
                        className="mt-1"
                      />
                      <p className="text-xs text-slate-500 mt-1">
                        Comma-separated. Leave empty to allow all IPs.
                      </p>
                    </div>

                    <div>
                      <Label htmlFor="edit-rate-limit" className="text-sm font-medium text-slate-700">
                        Rate Limit (requests/minute)
                      </Label>
                      <Input
                        id="edit-rate-limit"
                        type="number"
                        value={rateLimit}
                        onChange={(e) => setRateLimit(e.target.value)}
                        placeholder="e.g., 60"
                        className="mt-1"
                      />
                      <p className="text-xs text-slate-500 mt-1">Custom rate limit for this key</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex space-x-3 mt-6 flex-shrink-0">
              <Button
                onClick={handleEditCancel}
                variant="outline"
                className="flex-1 rounded-xl"
              >
                Cancel
              </Button>
              <Button
                onClick={handleEditSave}
                disabled={isSubmitting || !keyName.trim()}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-xl disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save Changes'
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
