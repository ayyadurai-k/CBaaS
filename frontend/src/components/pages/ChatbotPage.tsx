
import React, { useState } from 'react';
import { Send, MessageSquare, FileText, Clock, Settings, Check, Key, TestTube } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { toast } from '@/hooks/use-toast';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: string;
  sources?: string[];
}

interface Document {
  id: string;
  name: string;
  connected: boolean;
}

const mockMessages: Message[] = [
  {
    id: '1',
    type: 'bot',
    content: 'Hello! I\'m your company chatbot. I can help you find information from your uploaded documents. What would you like to know?',
    timestamp: '14:30',
  }
];

const mockDocuments: Document[] = [
  { id: '1', name: 'Employee Handbook.pdf', connected: true },
  { id: '2', name: 'Company Policies.pdf', connected: true },
  { id: '3', name: 'Technical Documentation.pdf', connected: false },
  { id: '4', name: 'Product Manual.pdf', connected: true },
  { id: '5', name: 'FAQ Document.pdf', connected: false },
];

const llmProviders = {
  openai: {
    name: 'OpenAI',
    models: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o']
  },
  gemini: {
    name: 'Google Gemini',
    models: ['gemini-pro']
  },
  deepseek: {
    name: 'DeepSeek',
    models: ['deepseek-chat', 'deepseek-coder']
  }
};

export const ChatbotPage: React.FC = () => {
  const [chatbotName, setChatbotName] = useState('Customer Support Bot');
  const [tone, setTone] = useState('professional');
  const [systemInstructions, setSystemInstructions] = useState('You are a helpful customer support assistant. Be polite, professional, and provide accurate information based on the company documents. If you don\'t know something, ask the user to contact support directly.');
  const [documents, setDocuments] = useState<Document[]>(mockDocuments);
  const [messages, setMessages] = useState<Message[]>(mockMessages);
  const [inputValue, setInputValue] = useState('');

  // LLM Provider state
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [selectedModel, setSelectedModel] = useState('gpt-3.5-turbo');
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [llmSystemPrompt, setLlmSystemPrompt] = useState('');

  const handleDocumentToggle = (documentId: string) => {
    setDocuments(documents.map(doc => 
      doc.id === documentId 
        ? { ...doc, connected: !doc.connected }
        : doc
    ));
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const botResponse: Message = {
      id: (Date.now() + 1).toString(),
      type: 'bot',
      content: 'Based on our company handbook, employees are entitled to 15 days of paid vacation per year. You can request time off through our HR portal or by contacting your manager directly.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      sources: ['Employee Handbook.pdf', 'Company Policies.pdf']
    };

    setMessages(prev => [...prev, userMessage, botResponse]);
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    setSelectedModel(llmProviders[provider as keyof typeof llmProviders].models[0]);
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

    toast({
      title: "Testing API Key...",
      description: "Validating your API key with the provider",
    });

    // Simulate API test
    setTimeout(() => {
      toast({
        title: "Success",
        description: "API key is valid and working",
      });
    }, 2000);
  };

  const connectedDocuments = documents.filter(doc => doc.connected);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Your Chatbot</h1>
          <p className="text-slate-600 mt-2">Configure and test your AI assistant</p>
        </div>
        <Button>
          <Settings className="w-4 h-4 mr-2" />
          Save Changes
        </Button>
      </div>

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
                    onChange={(e) => setTone(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="professional">Professional</option>
                    <option value="friendly">Friendly</option>
                    <option value="casual">Casual</option>
                    <option value="formal">Formal</option>
                    <option value="enthusiastic">Enthusiastic</option>
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
                  <select 
                    value={selectedProvider}
                    onChange={(e) => handleProviderChange(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {Object.entries(llmProviders).map(([key, provider]) => (
                      <option key={key} value={key}>{provider.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Model
                  </label>
                  <select 
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {llmProviders[selectedProvider as keyof typeof llmProviders].models.map((model) => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
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
                  >
                    <TestTube className="w-4 h-4 mr-2" />
                    Test API Key
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
              <div className="flex space-x-3">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Test your chatbot..."
                  className="flex-1 h-10 rounded-xl border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                />
                <Button
                  onClick={handleSendMessage}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
