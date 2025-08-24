
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Settings, Upload, TrendingUp, Users, List } from 'lucide-react';

const sections = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: TrendingUp,
    content: {
      title: 'Getting Started with ChatFlow',
      subsections: [
        {
          title: 'Quick Setup',
          content: `Welcome to ChatFlow! This guide will help you get your first chatbot up and running in minutes.

**Step 1: Create Your Account**
Sign up for a ChatFlow account and verify your email address.

**Step 2: Upload Your First Document**
Navigate to the Documents page and upload your knowledge base files (PDF, TXT, DOCX supported).

**Step 3: Create a Chatbot**
Go to the Chatbots page and click "Create New Chatbot". Follow the wizard to configure your bot.

**Step 4: Test Your Bot**
Use the preview function to test your chatbot before deploying it.`
        },
        {
          title: 'Best Practices',
          content: `- Keep your documents well-organized and up-to-date
- Use clear, descriptive names for your chatbots
- Test regularly with common user queries
- Monitor analytics to improve performance`
        }
      ]
    }
  },
  {
    id: 'authentication',
    title: 'Authentication & API Keys',
    icon: Settings,
    content: {
      title: 'Authentication & API Keys',
      subsections: [
        {
          title: 'API Key Management',
          content: `ChatFlow uses API keys for authentication. Each key has specific permissions and usage limits.

**Creating an API Key:**
1. Navigate to the API Keys page
2. Click "Generate New Key"
3. Set the appropriate permissions
4. Store your key securely - it won't be shown again

**Using Your API Key:**
Include your API key in the Authorization header:
\`\`\`
Authorization: Bearer YOUR_API_KEY
\`\`\`

**Key Types:**
- **Production Keys**: For live applications
- **Development Keys**: For testing and development
- **Read-only Keys**: For analytics and monitoring`
        }
      ]
    }
  },
  {
    id: 'uploading-files',
    title: 'Uploading Files',
    icon: Upload,
    content: {
      title: 'Document Management',
      subsections: [
        {
          title: 'Supported File Types',
          content: `ChatFlow supports the following file formats:
- PDF (.pdf)
- Text files (.txt)
- Word documents (.docx)
- Markdown (.md)

**File Size Limits:**
- Maximum file size: 10MB
- Maximum total storage: 1GB (varies by plan)

**Best Practices:**
- Use clear, descriptive filenames
- Organize files by topic or category
- Keep documents updated and relevant
- Remove outdated information regularly`
        }
      ]
    }
  },
  {
    id: 'query-api',
    title: 'Query API',
    icon: FileText,
    content: {
      title: 'Query API Reference',
      subsections: [
        {
          title: 'Making Queries',
          content: `The Query API allows you to send messages to your chatbot and receive responses.

**Endpoint:** \`POST /api/v1/chat\`

**Request Body:**
\`\`\`json
{
  "message": "User's question",
  "bot_id": "your-bot-id",
  "user_id": "unique-user-identifier",
  "context": "optional-context"
}
\`\`\`

**Response:**
\`\`\`json
{
  "response": "Bot's response",
  "bot_id": "your-bot-id",
  "timestamp": "2024-01-10T15:30:00Z",
  "tokens_used": 15,
  "confidence": 0.95
}
\`\`\``
        }
      ]
    }
  },
  {
    id: 'prompt-engineering',
    title: 'Prompt Engineering Tips',
    icon: List,
    content: {
      title: 'Prompt Engineering Best Practices',
      subsections: [
        {
          title: 'Writing Effective Prompts',
          content: `Good prompts lead to better chatbot responses. Here are key tips:

**Be Specific:**
- Use clear, specific language
- Provide context when needed
- Avoid ambiguous terms

**Set the Tone:**
- Define how formal or casual the bot should be
- Specify the expertise level
- Set personality traits

**Example System Instructions:**
"You are a helpful customer support assistant. Be friendly but professional. If you don't know an answer, admit it and offer to escalate to a human agent."`
        }
      ]
    }
  },
  {
    id: 'rate-limits',
    title: 'Rate Limits',
    icon: TrendingUp,
    content: {
      title: 'API Rate Limits',
      subsections: [
        {
          title: 'Understanding Limits',
          content: `Rate limits prevent abuse and ensure fair usage across all users.

**Free Plan:**
- 100 requests per hour
- 1,000 requests per month

**Pro Plan:**
- 1,000 requests per hour
- 50,000 requests per month

**Enterprise Plan:**
- Custom limits based on agreement

**Rate Limit Headers:**
- \`X-RateLimit-Limit\`: Total requests allowed
- \`X-RateLimit-Remaining\`: Requests remaining
- \`X-RateLimit-Reset\`: When the limit resets`
        }
      ]
    }
  }
];

export const DocumentationPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState('getting-started');
  const [isDarkMode, setIsDarkMode] = useState(false);

  const currentSection = sections.find(s => s.id === activeSection);

  return (
    <div className="flex h-full">
      {/* Sticky Sidebar */}
      <div className="sticky top-0 h-screen w-64 border-r border-slate-200 bg-slate-50 p-6 overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-slate-900">Documentation</h2>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsDarkMode(!isDarkMode)}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </Button>
        </div>
        
        <nav className="space-y-2">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-left transition-colors ${
                  activeSection === section.id
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium text-sm">{section.title}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">
              Platform Documentation
            </h1>
            <p className="text-slate-600 mt-2">
              Complete guide to using the ChatFlow platform
            </p>
          </div>

          {currentSection && (
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-slate-900 mb-4">
                  {currentSection.content.title}
                </h2>
              </div>

              {currentSection.content.subsections.map((subsection, index) => (
                <Card key={index} className="border-slate-200">
                  <CardHeader>
                    <CardTitle className="text-xl text-slate-900">
                      {subsection.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-slate max-w-none">
                      <pre className="whitespace-pre-wrap text-slate-700 leading-relaxed">
                        {subsection.content}
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Version Info */}
          <Card className="mt-12 border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Version Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-slate-600">
                <p><strong>API Version:</strong> v1.0</p>
                <p><strong>Last Updated:</strong> January 10, 2024</p>
                <p><strong>Documentation Version:</strong> 1.2.0</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
