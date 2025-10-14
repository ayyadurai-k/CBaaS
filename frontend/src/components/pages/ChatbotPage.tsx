
import React, { useState, useEffect } from 'react';
import { Send, MessageSquare, FileText, Clock, Settings, Check, Key, TestTube, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { toast } from '@/hooks/use-toast';
import { llmProvidersService } from '@/services/llm/llmProvidersService';
import { LLMProviderConfig } from '@/apis/llm/LLMProvidersAPI';
import { chatbotService, ChatbotConfig, ChatMessageData } from '@/services/ChatbotService';
import { DocumentInfo } from '@/apis/ChatbotAPI';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: string;
  sources?: string[];
}

const initialMessage: Message = {
  id: '1',
  type: 'bot',
  content: 'Hello! I\'m your company chatbot. I can help you find information from your uploaded documents. What would you like to know?',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
};

export const ChatbotPage: React.FC = () => {
  // Chatbot configuration state
  const [chatbotConfig, setChatbotConfig] = useState<ChatbotConfig | null>(null);
  const [configLoading, setConfigLoading] = useState(true);
  const [configError, setConfigError] = useState<string | null>(null);

  // Form state (local edits before save)
  const [chatbotName, setChatbotName] = useState('');
  const [tone, setTone] = useState<'friendly' | 'technical' | 'formal' | 'professional'>('professional');
  const [systemInstructions, setSystemInstructions] = useState('');
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  
  // LLM Provider state
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [llmSystemPrompt, setLlmSystemPrompt] = useState('');
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([initialMessage]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  
  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  // Dynamic provider data
  const [llmProviders, setLlmProviders] = useState<LLMProviderConfig>({});
  const [providersLoading, setProvidersLoading] = useState(true);
  const [providersError, setProvidersError] = useState<string | null>(null);

  // Load chatbot configuration on mount
  useEffect(() => {
    loadChatbotConfig();
  }, []);

  // Load LLM providers on component mount
  useEffect(() => {
    const loadProviders = async () => {
      setProvidersLoading(true);
      setProvidersError(null);
      
      try {
        const result = await llmProvidersService.getProviderConfig();
        
        if (result.success && result.data) {
          setLlmProviders(result.data);
        } else {
          console.warn('LLM providers API failed, using fallback configuration');
          setLlmProviders(getFallbackProviders());
          setProvidersError(null);
        }
      } catch (error) {
        console.error('Critical error loading LLM providers:', error);
        setLlmProviders(getFallbackProviders());
        setProvidersError(null);
      } finally {
        setProvidersLoading(false);
      }
    };

    loadProviders();
  }, []);

  // Load chatbot configuration from backend
  const loadChatbotConfig = async () => {
    setConfigLoading(true);
    setConfigError(null);
    
    try {
      const config = await chatbotService.getConfig();
      
      if (config) {
        setChatbotConfig(config);
        // Populate form fields
        setChatbotName(config.name);
        setTone(config.tone);
        setSystemInstructions(config.system_instructions);
        setLlmSystemPrompt(config.llm_system_prompt);
        setDocuments(config.documents_available);
        
        // Set LLM provider settings
        if (config.llm_provider) {
          setSelectedProvider(config.llm_provider);
        }
        if (config.llm_model) {
          setSelectedModel(config.llm_model);
        }
      } else {
        // No chatbot configured yet - use defaults
        setConfigError('No chatbot configured. Please set up your chatbot.');
      }
    } catch (error: any) {
      console.error('Error loading chatbot config:', error);
      setConfigError(error.message || 'Failed to load chatbot configuration');
      toast({
        title: "Error",
        description: error.message || 'Failed to load chatbot configuration',
        variant: "destructive",
      });
    } finally {
      setConfigLoading(false);
    }
  };

  const getFallbackProviders = (): LLMProviderConfig => ({
    openai: {
      name: 'OpenAI',
      models: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o']
    },
    gemini: {
      name: 'Google Gemini',
      models: ['gemini-pro', 'gemini-2.0-flash-exp']
    },
    deepseek: {
      name: 'DeepSeek',
      models: ['deepseek-chat', 'deepseek-coder']
    }
  });

  const handleDocumentToggle = (documentId: string) => {
    setDocuments(documents.map(doc => 
      doc.id === documentId 
        ? { ...doc, connected: !doc.connected }
        : doc
    ));
  };

  const handleSaveConfiguration = async () => {
    setIsSaving(true);
    
    try {
      // Get connected document IDs
      const connectedDocIds = documents
        .filter(doc => doc.connected)
        .map(doc => doc.id);
      
      // Build update payload
      const payload: any = {
        name: chatbotName,
        tone: tone,
        system_instructions: systemInstructions,
        llm_system_prompt: llmSystemPrompt,
        documents_connected: connectedDocIds,
      };
      
      // Only include LLM settings if they're set
      if (selectedProvider) {
        payload.llm_provider = selectedProvider;
      }
      if (selectedModel) {
        payload.llm_model = selectedModel;
      }
      if (apiKey) {
        payload.llm_api_key = apiKey;
        payload.llm_is_active = true;
      }
      
      const updatedConfig = await chatbotService.updateConfig(payload);
      setChatbotConfig(updatedConfig);
      
      toast({
        title: "Success",
        description: "Chatbot configuration saved successfully",
      });
      
      // Clear API key field after save (security best practice)
      setApiKey('');
      
    } catch (error: any) {
      console.error('Error saving configuration:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to save configuration",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    
    // Check if chatbot is configured
    if (!chatbotConfig?.is_fully_configured) {
      toast({
        title: "Chatbot Not Configured",
        description: "Please configure your chatbot with an LLM provider first",
        variant: "destructive",
      });
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsSending(true);

    try {
      // Convert messages to API format
      const history: ChatMessageData[] = messages.map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp,
      }));

      const result = await chatbotService.sendMessage({
        message: inputValue,
        history: history,
      });

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: result.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: result.sources,
      };

      setMessages(prev => [...prev, botResponse]);
      
    } catch (error: any) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: `Sorry, I encountered an error: ${error.message}. Please try again.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
      toast({
        title: "Error",
        description: error.message || "Failed to send message",
        variant: "destructive",
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    if (llmProviders[provider]?.models?.length > 0) {
      setSelectedModel(llmProviders[provider].models[0]);
    }
  };

  const handleTestApiKey = async () => {
    if (!apiKey) {
      toast({
        title: "Error",
        description: "Please enter an API key first",
        variant: "destructive",
      });
      return;
    }

    if (!selectedProvider || !selectedModel) {
      toast({
        title: "Error",
        description: "Please select a provider and model first",
        variant: "destructive",
      });
      return;
    }

    setIsTesting(true);

    try {
      const result = await chatbotService.testApiKey({
        provider: selectedProvider,
        model_name: selectedModel,
        api_key: apiKey,
      });

      if (result.success) {
        toast({
          title: "Success ✓",
          description: result.message,
        });
      } else {
        toast({
          title: "Test Failed",
          description: result.message,
          variant: "destructive",
        });
      }
    } catch (error: any) {
      console.error('Error testing API key:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to test API key",
        variant: "destructive",
      });
    } finally {
      setIsTesting(false);
    }
  };

  const connectedDocuments = documents.filter(doc => doc.connected);

  // Show loading state
  if (configLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-slate-600">Loading chatbot configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Your Chatbot</h1>
          <p className="text-slate-600 mt-2">Configure and test your AI assistant</p>
          {chatbotConfig?.is_fully_configured && (
            <div className="flex items-center mt-2 text-sm text-green-600">
              <Check className="w-4 h-4 mr-1" />
              Configured and ready
            </div>
          )}
        </div>
        <Button 
          onClick={handleSaveConfiguration}
          disabled={isSaving}
        >
          {isSaving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Settings className="w-4 h-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>

      {configError && !chatbotConfig && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-amber-900">Setup Required</h3>
                <p className="text-sm text-amber-700 mt-1">{configError}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Combined Configuration Panel */}
        <div className="space-y-6">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Configuration</CardTitle>
              <p className="text-sm text-slate-600">Set up your chatbot's settings and behavior</p>
            </CardHeader>
            <CardContent className="space-y-8">
              {/* Basic Configuration Section */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">Basic Configuration</h3>
                  <p className="text-sm text-slate-600 mb-6">Set up your chatbot's identity and behavior</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Chatbot Name
                  </label>
                  <Input
                    value={chatbotName}
                    onChange={(e) => setChatbotName(e.target.value)}
                    placeholder="Enter chatbot name"
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Tone
                  </label>
                  <select 
                    value={tone}
                    onChange={(e) => setTone(e.target.value as 'friendly' | 'technical' | 'formal' | 'professional')}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="professional">Professional</option>
                    <option value="friendly">Friendly</option>
                    <option value="technical">Technical</option>
                    <option value="formal">Formal</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    System Instructions
                  </label>
                  <Textarea
                    value={systemInstructions}
                    onChange={(e) => setSystemInstructions(e.target.value)}
                    placeholder="Enter system instructions for your chatbot"
                    className="w-full min-h-[120px]"
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    These instructions define how your chatbot should behave and respond to users.
                  </p>
                </div>
              </div>

              <Separator />

              {/* LLM Provider Settings Section */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">LLM Provider Settings</h3>
                  <p className="text-sm text-slate-600 mb-6">Configure your AI model provider and settings</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Choose your model provider
                  </label>
                  {providersLoading ? (
                    <div className="flex items-center space-x-2 px-3 py-2 border border-slate-300 rounded-xl bg-slate-50">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm text-slate-500">Loading providers...</span>
                    </div>
                  ) : providersError ? (
                    <div className="px-3 py-2 border border-red-300 rounded-xl bg-red-50 text-red-700 text-sm">
                      Error: {providersError}
                    </div>
                  ) : (
                    <select 
                      value={selectedProvider}
                      onChange={(e) => handleProviderChange(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={Object.keys(llmProviders).length === 0}
                    >
                      {Object.entries(llmProviders).map(([key, provider]) => (
                        <option key={key} value={key}>{provider.name}</option>
                      ))}
                    </select>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Model
                  </label>
                  {providersLoading ? (
                    <div className="flex items-center space-x-2 px-3 py-2 border border-slate-300 rounded-xl bg-slate-50">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm text-slate-500">Loading models...</span>
                    </div>
                  ) : providersError ? (
                    <div className="px-3 py-2 border border-red-300 rounded-xl bg-red-50 text-red-700 text-sm">
                      No models available
                    </div>
                  ) : (
                    <select 
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={!llmProviders[selectedProvider]?.models?.length}
                    >
                      {(llmProviders[selectedProvider]?.models || []).map((model) => (
                        <option key={model} value={model}>{model}</option>
                      ))}
                    </select>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    API Key
                  </label>
                  <div className="relative">
                    <Input
                      type={showApiKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter your API key"
                      className="w-full pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-500 hover:text-slate-700"
                    >
                      {showApiKey ? '🙈' : '👁️'}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    System Prompt (Optional)
                  </label>
                  <Textarea
                    value={llmSystemPrompt}
                    onChange={(e) => setLlmSystemPrompt(e.target.value)}
                    placeholder="Enter additional system prompt for the LLM"
                    className="w-full min-h-[100px]"
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    This will be added to the base system prompt for more specific behavior.
                  </p>
                </div>

                <div className="flex justify-center">
                  <Button
                    onClick={handleTestApiKey}
                    variant="outline"
                    className="w-full max-w-xs"
                    disabled={isTesting || !apiKey}
                  >
                    {isTesting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Testing...
                      </>
                    ) : (
                      <>
                        <TestTube className="w-4 h-4 mr-2" />
                        Test API Key
                      </>
                    )}
                  </Button>
                </div>
              </div>

              <Separator />

              {/* Connected Documents Section */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">Connected Documents</h3>
                  <p className="text-sm text-slate-600 mb-6">Select which documents your chatbot can reference</p>
                </div>

                <div className="space-y-3">
                  {documents.map((document) => (
                    <div key={document.id} className="flex items-center space-x-3 p-3 bg-slate-50 rounded-xl">
                      <Checkbox
                        id={document.id}
                        checked={document.connected}
                        onCheckedChange={() => handleDocumentToggle(document.id)}
                      />
                      <div className="flex-1 flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-slate-500" />
                        <label 
                          htmlFor={document.id}
                          className="text-sm font-medium text-slate-700 cursor-pointer"
                        >
                          {document.name}
                        </label>
                      </div>
                      {document.connected && (
                        <Check className="w-4 h-4 text-green-600" />
                      )}
                    </div>
                  ))}
                </div>
                <div className="p-3 bg-blue-50 rounded-xl">
                  <p className="text-sm text-blue-700">
                    <strong>{connectedDocuments.length}</strong> documents connected
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Test Chat Panel */}
        <div className="lg:col-span-1">
          <Card className="border-slate-200 h-[600px] flex flex-col">
            <CardHeader className="border-b border-slate-200 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                  <MessageSquare className="w-5 h-5 text-white" />
                </div>
                <div>
                  <CardTitle className="text-slate-900">{chatbotName}</CardTitle>
                  <p className="text-sm text-slate-600">Test your chatbot configuration</p>
                </div>
              </div>
            </CardHeader>

            {/* Messages */}
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-slate-100 text-slate-900'
                  }`}>
                    <p className="text-sm">{message.content}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className={`text-xs ${message.type === 'user' ? 'text-blue-100' : 'text-slate-500'}`}>
                        {message.timestamp}
                      </span>
                    </div>
                    {message.sources && (
                      <div className="mt-2 pt-2 border-t border-slate-200">
                        <p className="text-xs text-slate-600 mb-1">Sources:</p>
                        {message.sources.map((source, index) => (
                          <div key={index} className="flex items-center text-xs text-slate-600 mb-1">
                            <FileText className="w-3 h-3 mr-1" />
                            {source}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>

            {/* Input */}
            <div className="p-4 border-t border-slate-200">
              {!chatbotConfig?.is_fully_configured && (
                <div className="mb-3 p-2 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-xs text-amber-700 text-center">
                    Configure your chatbot with an LLM provider to start testing
                  </p>
                </div>
              )}
              <div className="flex space-x-3">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={chatbotConfig?.is_fully_configured ? "Test your chatbot..." : "Configure chatbot first..."}
                  className="flex-1 h-10 rounded-xl border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                  disabled={isSending || !chatbotConfig?.is_fully_configured}
                />
                <Button
                  onClick={handleSendMessage}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl"
                  disabled={isSending || !inputValue.trim() || !chatbotConfig?.is_fully_configured}
                >
                  {isSending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
