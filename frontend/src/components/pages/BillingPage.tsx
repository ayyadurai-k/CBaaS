
import React, { useState } from 'react';
import { CreditCard, Download, Plus, Crown, Zap, Building } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/hooks/use-toast';

interface Invoice {
  id: string;
  date: string;
  invoiceId: string;
  amount: string;
  status: 'paid' | 'pending' | 'failed';
}

const mockInvoices: Invoice[] = [
  {
    id: '1',
    date: '2024-01-15',
    invoiceId: 'INV-2024-001',
    amount: '$29.00',
    status: 'paid'
  },
  {
    id: '2',
    date: '2024-01-01',
    invoiceId: 'INV-2024-002',
    amount: '$29.00',
    status: 'paid'
  }
];

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    icon: Building,
    features: [
      '1 chatbot',
      '100 queries/month',
      '5 documents',
      'Email support'
    ],
    current: true
  },
  {
    name: 'Pro',
    price: '$29',
    period: 'per month',
    icon: Zap,
    features: [
      '5 chatbots',
      '10,000 queries/month',
      '100 documents',
      'Priority support',
      'Custom branding'
    ],
    current: false
  },
  {
    name: 'Enterprise',
    price: '$99',
    period: 'per month',
    icon: Crown,
    features: [
      'Unlimited chatbots',
      'Unlimited queries',
      'Unlimited documents',
      '24/7 phone support',
      'Custom integrations',
      'SLA guarantee'
    ],
    current: false
  }
];

export const BillingPage: React.FC = () => {
  const [showPlanModal, setShowPlanModal] = useState(false);
  
  const currentPlan = plans.find(plan => plan.current) || plans[0];

  const getStatusBadge = (status: Invoice['status']) => {
    const styles = {
      paid: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800'
    };
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const handleDownloadInvoice = (invoiceId: string) => {
    toast({
      title: "Invoice downloaded",
      description: `Invoice ${invoiceId} has been downloaded`,
    });
  };

  const handleUpgradePlan = (planName: string) => {
    toast({
      title: "Redirecting to checkout",
      description: `Upgrading to ${planName} plan...`,
    });
    setShowPlanModal(false);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Billing & Usage</h1>
        <p className="text-slate-600">Manage your subscription and view billing history</p>
      </div>

      {/* Current Plan */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-slate-900">Current Plan</h2>
          <Button 
            onClick={() => setShowPlanModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl"
          >
            <Plus className="w-4 h-4 mr-2" />
            Upgrade Plan
          </Button>
        </div>
        
        <div className="flex items-center space-x-4 mb-6">
          <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center">
            <currentPlan.icon className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">{currentPlan.name} Plan</h3>
            <p className="text-slate-600">{currentPlan.price} {currentPlan.period}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-50 rounded-xl p-4">
            <div className="text-2xl font-bold text-slate-900 mb-1">1,245</div>
            <div className="text-sm text-slate-600">Queries this month</div>
            <div className="text-xs text-slate-500 mt-1">100 remaining</div>
          </div>
          <div className="bg-slate-50 rounded-xl p-4">
            <div className="text-2xl font-bold text-slate-900 mb-1">3</div>
            <div className="text-sm text-slate-600">Documents uploaded</div>
            <div className="text-xs text-slate-500 mt-1">2 remaining</div>
          </div>
          <div className="bg-slate-50 rounded-xl p-4">
            <div className="text-2xl font-bold text-slate-900 mb-1">847</div>
            <div className="text-sm text-slate-600">API calls this month</div>
            <div className="text-xs text-slate-500 mt-1">Unlimited</div>
          </div>
        </div>
      </div>

      {/* Payment Method */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-900">Payment Method</h2>
          <Button variant="outline" className="rounded-xl">
            Update Payment Method
          </Button>
        </div>
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
            <CreditCard className="w-5 h-5 text-slate-600" />
          </div>
          <div>
            <div className="font-medium text-slate-900">•••• •••• •••• 4242</div>
            <div className="text-sm text-slate-600">Expires 12/26</div>
          </div>
        </div>
      </div>

      {/* Billing History */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-900">Billing History</h2>
            <Button variant="outline" className="rounded-xl">
              View All Invoices
            </Button>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Date</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Invoice ID</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Amount</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Status</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-900">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {mockInvoices.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-4 px-6 text-slate-900">{invoice.date}</td>
                  <td className="py-4 px-6 text-slate-600">{invoice.invoiceId}</td>
                  <td className="py-4 px-6 font-medium text-slate-900">{invoice.amount}</td>
                  <td className="py-4 px-6">{getStatusBadge(invoice.status)}</td>
                  <td className="py-4 px-6">
                    <button
                      onClick={() => handleDownloadInvoice(invoice.invoiceId)}
                      className="p-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Plan Selection Modal */}
      {showPlanModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-semibold text-slate-900">Choose Your Plan</h3>
              <button 
                onClick={() => setShowPlanModal(false)}
                className="text-slate-500 hover:text-slate-700 text-xl font-bold"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {plans.map((plan) => {
                const Icon = plan.icon;
                return (
                  <div
                    key={plan.name}
                    className={`border rounded-2xl p-6 ${
                      plan.current 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center space-x-3 mb-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        plan.current ? 'bg-blue-600' : 'bg-slate-100'
                      }`}>
                        <Icon className={`w-5 h-5 ${plan.current ? 'text-white' : 'text-slate-600'}`} />
                      </div>
                      <div>
                        <h4 className="font-semibold text-slate-900">{plan.name}</h4>
                        <p className="text-sm text-slate-600">{plan.price} {plan.period}</p>
                      </div>
                    </div>
                    
                    <ul className="space-y-2 mb-6">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="text-sm text-slate-600 flex items-center">
                          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full mr-3"></span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                    
                    <Button
                      onClick={() => handleUpgradePlan(plan.name)}
                      className={`w-full rounded-xl ${
                        plan.current 
                          ? 'bg-slate-300 text-slate-600 cursor-not-allowed' 
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}
                      disabled={plan.current}
                    >
                      {plan.current ? 'Current Plan' : 'Select Plan'}
                    </Button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
