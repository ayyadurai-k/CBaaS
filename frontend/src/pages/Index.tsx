import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { MessageSquare, Bot, FileText, BarChart3, Users, Key } from 'lucide-react';

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex justify-center mb-8">
            <div className="flex items-center gap-3 bg-white rounded-2xl px-6 py-3 shadow-lg border border-slate-200">
              <MessageSquare className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-slate-900">CBaaS</h1>
            </div>
          </div>
          
          <h2 className="text-5xl font-bold text-slate-900 mb-6 leading-tight">
            Chatbot as a Service
            <span className="block text-blue-600">Platform</span>
          </h2>
          
          <p className="text-xl text-slate-600 mb-8 leading-relaxed max-w-2xl mx-auto">
            Build, deploy, and manage intelligent chatbots with ease. Our comprehensive platform provides everything you need to create conversational AI solutions for your business.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/signup">
              <Button size="lg" className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg rounded-xl">
                Get Started Free
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="w-full sm:w-auto px-8 py-4 text-lg rounded-xl border-slate-300">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h3 className="text-3xl font-bold text-slate-900 mb-4">
            Everything you need to build chatbots
          </h3>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            From document processing to analytics, our platform provides comprehensive tools for chatbot development and management.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div className="bg-white rounded-2xl p-8 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="bg-blue-100 rounded-xl p-3 w-fit mb-4">
              <Bot className="h-6 w-6 text-blue-600" />
            </div>
            <h4 className="text-xl font-semibold text-slate-900 mb-3">Smart Chatbots</h4>
            <p className="text-slate-600">
              Create intelligent conversational AI powered by advanced language models and custom training data.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="bg-green-100 rounded-xl p-3 w-fit mb-4">
              <FileText className="h-6 w-6 text-green-600" />
            </div>
            <h4 className="text-xl font-semibold text-slate-900 mb-3">Document Processing</h4>
            <p className="text-slate-600">
              Upload and process documents to train your chatbots with your specific knowledge base and content.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="bg-purple-100 rounded-xl p-3 w-fit mb-4">
              <BarChart3 className="h-6 w-6 text-purple-600" />
            </div>
            <h4 className="text-xl font-semibold text-slate-900 mb-3">Analytics & Insights</h4>
            <p className="text-slate-600">
              Track performance, user interactions, and gain valuable insights to improve your chatbot experience.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="bg-orange-100 rounded-xl p-3 w-fit mb-4">
              <Users className="h-6 w-6 text-orange-600" />
            </div>
            <h4 className="text-xl font-semibold text-slate-900 mb-3">Team Collaboration</h4>
            <p className="text-slate-600">
              Work together with your team to build, test, and deploy chatbots with role-based access controls.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="bg-red-100 rounded-xl p-3 w-fit mb-4">
              <Key className="h-6 w-6 text-red-600" />
            </div>
            <h4 className="text-xl font-semibold text-slate-900 mb-3">API Integration</h4>
            <p className="text-slate-600">
              Seamlessly integrate your chatbots into existing applications with our robust API and SDK support.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
            <div className="bg-indigo-100 rounded-xl p-3 w-fit mb-4">
              <MessageSquare className="h-6 w-6 text-indigo-600" />
            </div>
            <h4 className="text-xl font-semibold text-slate-900 mb-3">Live Chat</h4>
            <p className="text-slate-600">
              Enable real-time conversations with your users through our responsive chat interface and components.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="bg-slate-900 rounded-3xl p-12 text-center">
          <h3 className="text-3xl font-bold text-white mb-4">
            Ready to build your first chatbot?
          </h3>
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Join thousands of developers and businesses using CBaaS to create intelligent conversational experiences.
          </p>
          <Link to="/signup">
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg rounded-xl">
              Start Building Today
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Index;
