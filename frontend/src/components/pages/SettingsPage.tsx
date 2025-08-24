
import React, { useState } from 'react';
import { Upload, AlertTriangle, Building, CreditCard, Shield, X, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';

export const SettingsPage: React.FC = () => {
  const [orgSettings, setOrgSettings] = useState({
    name: 'Acme Corp',
    logo: null as File | null
  });

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);

  const handleLogoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        toast({
          title: "Invalid file type",
          description: "Please select a PNG, JPG, or WEBP image",
          variant: "destructive",
        });
        return;
      }

      // Validate file size (1MB max)
      const maxSize = 1 * 1024 * 1024; // 1MB in bytes
      if (file.size > maxSize) {
        toast({
          title: "File too large",
          description: "Image size must be less than 1MB",
          variant: "destructive",
        });
        return;
      }

      setOrgSettings({ ...orgSettings, logo: file });
      
      // Create preview URL
      const reader = new FileReader();
      reader.onload = (e) => {
        setLogoPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveLogo = () => {
    setOrgSettings({ ...orgSettings, logo: null });
    setLogoPreview(null);
    // Reset file input
    const fileInput = document.getElementById('orgLogo') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const handleSaveChanges = () => {
    toast({
      title: "Settings saved",
      description: "Your organization settings have been updated successfully",
    });
  };

  const handleDeleteOrg = () => {
    console.log('Organization deleted');
    setShowDeleteModal(false);
    toast({
      title: "Organization deleted",
      description: "Your organization has been permanently deleted",
      variant: "destructive",
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Organization Settings</h1>
        <p className="text-slate-600">Manage your organization preferences and billing</p>
      </div>

      <div className="space-y-8">
        {/* Organization Details */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
              <Building className="w-5 h-5 text-blue-600" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900">Organization Details</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="orgName" className="text-sm font-medium text-slate-700">
                Organization Name
              </Label>
              <Input
                id="orgName"
                value={orgSettings.name}
                onChange={(e) => setOrgSettings({ ...orgSettings, name: e.target.value })}
                className="h-12 rounded-xl border-slate-300 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="orgLogo" className="text-sm font-medium text-slate-700">
                Organization Logo
              </Label>
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-slate-100 rounded-xl flex items-center justify-center overflow-hidden">
                  {logoPreview ? (
                    <img
                      src={logoPreview}
                      alt="Organization Logo"
                      className="w-full h-full object-cover rounded-xl"
                    />
                  ) : (
                    <Building className="w-6 h-6 text-slate-500" />
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <input
                    id="orgLogo"
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/webp"
                    onChange={handleLogoUpload}
                    className="hidden"
                  />
                  <div className="flex space-x-2">
                    <Button
                      type="button"
                      onClick={() => document.getElementById('orgLogo')?.click()}
                      variant="outline"
                      className="rounded-xl"
                      size="sm"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      {logoPreview ? 'Replace' : 'Upload'} Logo
                    </Button>
                    {logoPreview && (
                      <Button
                        type="button"
                        onClick={handleRemoveLogo}
                        variant="outline"
                        className="rounded-xl text-red-600 hover:text-red-700 hover:bg-red-50"
                        size="sm"
                      >
                        <X className="w-4 h-4 mr-2" />
                        Remove
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    Max 1MB • PNG, JPG, WEBP recommended
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-slate-200">
            <Button 
              onClick={handleSaveChanges}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium"
            >
              <Check className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
          </div>
        </div>

        {/* Billing Information */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center">
              <CreditCard className="w-5 h-5 text-green-600" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900">Billing & Plan</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 border border-slate-200 rounded-xl">
              <h3 className="font-semibold text-slate-900 mb-2">Free</h3>
              <p className="text-2xl font-bold text-slate-900 mb-2">$0<span className="text-sm font-normal text-slate-600">/month</span></p>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• 1,000 API calls/month</li>
                <li>• 5 documents max</li>
                <li>• Basic support</li>
              </ul>
            </div>

            <div className="p-4 border-2 border-blue-600 rounded-xl bg-blue-50">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-slate-900">Pro</h3>
                <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded-full">Current</span>
              </div>
              <p className="text-2xl font-bold text-slate-900 mb-2">$49<span className="text-sm font-normal text-slate-600">/month</span></p>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• 25,000 API calls/month</li>
                <li>• 100 documents max</li>
                <li>• Priority support</li>
              </ul>
            </div>

            <div className="p-4 border border-slate-200 rounded-xl">
              <h3 className="font-semibold text-slate-900 mb-2">Enterprise</h3>
              <p className="text-2xl font-bold text-slate-900 mb-2">$199<span className="text-sm font-normal text-slate-600">/month</span></p>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• Unlimited API calls</li>
                <li>• Unlimited documents</li>
                <li>• White-label option</li>
              </ul>
            </div>
          </div>

          <Button variant="outline" className="rounded-xl">
            Manage Billing
          </Button>
        </div>

        {/* Danger Zone */}
        <div className="bg-white rounded-2xl shadow-sm border border-red-200 p-6">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <h2 className="text-xl font-semibold text-red-900">Danger Zone</h2>
          </div>

          <div className="p-4 border border-red-200 rounded-xl bg-red-50">
            <h3 className="font-semibold text-red-900 mb-2">Delete Organization</h3>
            <p className="text-sm text-red-700 mb-4">
              This action cannot be undone. All data, documents, and API keys will be permanently deleted.
            </p>
            <Button
              onClick={() => setShowDeleteModal(true)}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-xl"
            >
              Delete Organization
            </Button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Confirm Deletion</h3>
            </div>
            <p className="text-slate-600 mb-6">
              Are you sure you want to delete your organization? This action cannot be undone and all data will be permanently lost.
            </p>
            <div className="flex space-x-3">
              <Button
                onClick={() => setShowDeleteModal(false)}
                variant="outline"
                className="flex-1 rounded-xl"
              >
                Cancel
              </Button>
              <Button
                onClick={handleDeleteOrg}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white rounded-xl"
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
