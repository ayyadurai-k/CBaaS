
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { X } from 'lucide-react';

interface CreateChatbotModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateChatbotModal: React.FC<CreateChatbotModalProps> = ({ isOpen, onClose }) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    tone: 'friendly',
    documents: [],
    instructions: '',
  });

  if (!isOpen) return null;

  const handleNext = () => setStep(step + 1);
  const handleBack = () => setStep(step - 1);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Create New Chatbot</CardTitle>
          <Button variant="outline" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Step 1: Basic Information */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Basic Information</h3>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Chatbot Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Customer Support Bot"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Tone
                </label>
                <select
                  value={formData.tone}
                  onChange={(e) => setFormData({...formData, tone: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="friendly">Friendly</option>
                  <option value="technical">Technical</option>
                  <option value="formal">Formal</option>
                </select>
              </div>
            </div>
          )}

          {/* Step 2: Document Selection */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Select Documents</h3>
              <div className="space-y-3">
                {['FAQ Document', 'Product Manual', 'Technical Documentation', 'Employee Handbook'].map((doc) => (
                  <div key={doc} className="flex items-center space-x-3 p-3 border border-slate-200 rounded-xl">
                    <input type="checkbox" id={doc} className="rounded" />
                    <label htmlFor={doc} className="flex-1 cursor-pointer">{doc}</label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: System Instructions */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">System Instructions</h3>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Custom Instructions (Optional)
                </label>
                <textarea
                  value={formData.instructions}
                  onChange={(e) => setFormData({...formData, instructions: e.target.value})}
                  rows={6}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Provide specific instructions for how the chatbot should behave..."
                />
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button
              variant="outline"
              onClick={step === 1 ? onClose : handleBack}
            >
              {step === 1 ? 'Cancel' : 'Back'}
            </Button>
            <Button
              onClick={step === 3 ? onClose : handleNext}
            >
              {step === 3 ? 'Create Chatbot' : 'Next'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
