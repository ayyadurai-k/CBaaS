import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  AlertTriangle, 
  Building, 
  User as UserIcon,
  X, 
  Check,
  Loader2,
  Camera,
  Trash2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { useProfile } from '@/hooks/redux/useProfile';
import { useOrganization } from '@/hooks/useOrganization';
import { UpdateProfilePayload } from '@/apis/UsersAPI';
import { toast } from '@/hooks/use-toast';

type TabType = 'profile' | 'organization';

export const SettingsPage: React.FC = () => {
  const {
    profile,
    isLoading: profileLoading,
    isUpdating: profileUpdating,
    isUploadingPicture,
    updateProfile,
    uploadProfilePicture,
    deleteProfilePicture,
    initials,
    avatarUrl,
  } = useProfile();

  const {
    organization,
    isLoading: orgLoading,
    isUpdating: orgUpdating,
    isUploadingLogo,
    updateOrganization,
    uploadOrganizationLogo,
    deleteOrganizationLogo,
    deleteOrganization,
  } = useOrganization();

  const [activeTab, setActiveTab] = useState<TabType>('profile');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [profilePicturePreview, setProfilePicturePreview] = useState<string | null>(null);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isEditingOrg, setIsEditingOrg] = useState(false);
  
  // Form states
  const [profileForm, setProfileForm] = useState({
    name: '',
    phone_number: '',
  });
  
  const [orgForm, setOrgForm] = useState({
    name: '',
  });

  // Initialize form data when profile/organization loads
  useEffect(() => {
    if (profile) {
      setProfileForm({
        name: profile.name || '',
        phone_number: profile.phone_number || '',
      });
    }
  }, [profile]);

  useEffect(() => {
    if (organization) {
      setOrgForm({
        name: organization.name || '',
      });
    }
  }, [organization]);

  const formatDate = (dateString: string | Date) => {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role.toLowerCase()) {
      case "owner":
        return "default";
      case "admin":
        return "secondary";
      case "member":
        return "outline";
      default:
        return "outline";
    }
  };

  // Profile handlers
  const handleProfileSave = async () => {
    if (!profile) return;
    
    const payload: UpdateProfilePayload = {};
    
    if (profileForm.name !== profile.name) {
      payload.name = profileForm.name;
    }
    
    if (profileForm.phone_number !== (profile.phone_number || '')) {
      payload.phone_number = profileForm.phone_number || undefined;
    }
    
    if (Object.keys(payload).length > 0) {
      const success = await updateProfile(payload);
      if (success) {
        setIsEditingProfile(false);
        toast({
          title: "Profile updated",
          description: "Your profile has been updated successfully",
        });
      }
    } else {
      setIsEditingProfile(false);
    }
  };

  const handleProfileCancel = () => {
    if (profile) {
      setProfileForm({
        name: profile.name || '',
        phone_number: profile.phone_number || '',
      });
    }
    setIsEditingProfile(false);
    setProfilePicturePreview(null);
  };

  const handleProfilePictureUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
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

      // Validate file size (5MB max)
      const maxSize = 5 * 1024 * 1024; // 5MB in bytes
      if (file.size > maxSize) {
        toast({
          title: "File too large",
          description: "Image size must be less than 5MB",
          variant: "destructive",
        });
        return;
      }

      uploadProfilePicture(file);
      
      // Create preview URL
      const reader = new FileReader();
      reader.onload = (e) => {
        setProfilePicturePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveProfilePicture = async () => {
    const success = await deleteProfilePicture();
    if (success) {
      setProfilePicturePreview(null);
      // Reset file input
      const fileInput = document.getElementById('profilePicture') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
    }
  };

  // Organization handlers
  const handleOrgSave = async () => {
    if (!organization) return;
    
    if (orgForm.name !== organization.name) {
      const success = await updateOrganization({ name: orgForm.name });
      if (success) {
        setIsEditingOrg(false);
      }
    } else {
      setIsEditingOrg(false);
    }
  };

  const handleOrgCancel = () => {
    if (organization) {
      setOrgForm({
        name: organization.name || '',
      });
    }
    setIsEditingOrg(false);
    setLogoPreview(null);
  };

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

      // Validate file size (5MB max)
      const maxSize = 5 * 1024 * 1024; // 5MB in bytes
      if (file.size > maxSize) {
        toast({
          title: "File too large",
          description: "Image size must be less than 5MB",
          variant: "destructive",
        });
        return;
      }

      uploadOrganizationLogo(file);
      
      // Create preview URL
      const reader = new FileReader();
      reader.onload = (e) => {
        setLogoPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveLogo = async () => {
    const success = await deleteOrganizationLogo();
    if (success) {
      setLogoPreview(null);
      // Reset file input
      const fileInput = document.getElementById('orgLogo') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
    }
  };

  const handleDeleteOrg = async () => {
    const success = await deleteOrganization();
    if (success) {
      setShowDeleteModal(false);
      // Redirect user or refresh data
      window.location.href = '/dashboard'; // or use router navigation
    }
  };

  if (profileLoading || orgLoading) {
    return (
      <div className="max-w-4xl mx-auto flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Settings</h1>
        <p className="text-slate-600">Manage your profile and organization settings</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-8 bg-slate-100 rounded-xl p-1">
        <button
          onClick={() => setActiveTab('profile')}
          className={`flex-1 px-4 py-2 rounded-lg font-medium text-sm transition-all ${
            activeTab === 'profile'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <UserIcon className="w-4 h-4 mr-2 inline" />
          Profile
        </button>
        <button
          onClick={() => setActiveTab('organization')}
          className={`flex-1 px-4 py-2 rounded-lg font-medium text-sm transition-all ${
            activeTab === 'organization'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Building className="w-4 h-4 mr-2 inline" />
          Organization
        </button>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && profile && (
        <div className="space-y-8">
          {/* Profile Information */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                  <UserIcon className="w-5 h-5 text-blue-600" />
                </div>
                <h2 className="text-xl font-semibold text-slate-900">Profile Information</h2>
              </div>
              {!isEditingProfile ? (
                <Button
                  onClick={() => setIsEditingProfile(true)}
                  variant="outline"
                  className="rounded-xl"
                >
                  Edit Profile
                </Button>
              ) : (
                <div className="flex space-x-2">
                  <Button
                    onClick={handleProfileCancel}
                    variant="outline"
                    className="rounded-xl"
                    disabled={profileUpdating}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleProfileSave}
                    className="rounded-xl"
                    disabled={profileUpdating}
                  >
                    {profileUpdating ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Check className="w-4 h-4 mr-2" />
                    )}
                    Save
                  </Button>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Profile Picture */}
              <div className="space-y-4">
                <Label className="text-sm font-medium text-slate-700">Profile Picture</Label>
                <div className="flex flex-col items-center space-y-4">
                  <Avatar className="w-24 h-24">
                    <AvatarImage
                      src={profilePicturePreview || avatarUrl || ""}
                      alt={profile.name || "User"}
                    />
                    <AvatarFallback className="text-xl font-semibold bg-slate-100 text-slate-700">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  
                  <div className="flex space-x-2">
                    <input
                      id="profilePicture"
                      type="file"
                      accept="image/jpeg,image/jpg,image/png,image/webp"
                      onChange={handleProfilePictureUpload}
                      className="hidden"
                    />
                    <Button
                      type="button"
                      onClick={() => document.getElementById('profilePicture')?.click()}
                      variant="outline"
                      className="rounded-xl"
                      size="sm"
                      disabled={isUploadingPicture}
                    >
                      {isUploadingPicture ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Camera className="w-4 h-4 mr-2" />
                      )}
                      {avatarUrl ? 'Change' : 'Upload'}
                    </Button>
                    
                    {avatarUrl && (
                      <Button
                        type="button"
                        onClick={handleRemoveProfilePicture}
                        variant="outline"
                        className="rounded-xl text-red-600 hover:text-red-700 hover:bg-red-50"
                        size="sm"
                        disabled={isUploadingPicture}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Remove
                      </Button>
                    )}
                  </div>
                  
                  <p className="text-xs text-slate-500 text-center">
                    Max 5MB • JPEG, PNG, WEBP
                  </p>
                </div>
              </div>

              {/* Profile Details */}
              <div className="lg:col-span-2 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-sm font-medium text-slate-700">
                      Full Name
                    </Label>
                    {isEditingProfile ? (
                      <Input
                        id="name"
                        value={profileForm.name}
                        onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                        className="h-12 rounded-xl border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                        placeholder="Enter your full name"
                      />
                    ) : (
                      <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 text-slate-900 flex items-center">
                        {profile.name}
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-sm font-medium text-slate-700">
                      Email Address
                    </Label>
                    <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 text-slate-500 flex items-center">
                      {profile.email}
                      <span className="ml-2 text-xs text-slate-400">(Cannot be changed)</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone" className="text-sm font-medium text-slate-700">
                      Phone Number
                    </Label>
                    {isEditingProfile ? (
                      <Input
                        id="phone"
                        value={profileForm.phone_number}
                        onChange={(e) => setProfileForm({ ...profileForm, phone_number: e.target.value })}
                        className="h-12 rounded-xl border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                        placeholder="Enter your phone number"
                      />
                    ) : (
                      <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 text-slate-900 flex items-center">
                        {profile.phone_number || 'Not provided'}
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-slate-700">
                      Role
                    </Label>
                    <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 flex items-center">
                      <Badge variant={getRoleBadgeVariant(profile.role)} className="capitalize">
                        {profile.role}
                      </Badge>
                      <span className="ml-2 text-xs text-slate-400">
                        (Managed by organization)
                      </span>
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-slate-700">
                      Member Since
                    </Label>
                    <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 text-slate-600 flex items-center">
                      {formatDate(profile.created_at)}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-slate-700">
                      Last Updated
                    </Label>
                    <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 text-slate-600 flex items-center">
                      {formatDate(profile.updated_at)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Organization Tab */}
      {activeTab === 'organization' && (
        <div className="space-y-8">
          {organization ? (
            <>
              {/* Organization Details */}
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center">
                      <Building className="w-5 h-5 text-green-600" />
                    </div>
                    <h2 className="text-xl font-semibold text-slate-900">Organization Details</h2>
                  </div>
                  {!isEditingOrg ? (
                    <Button
                      onClick={() => setIsEditingOrg(true)}
                      variant="outline"
                      className="rounded-xl"
                    >
                      Edit Organization
                    </Button>
                  ) : (
                    <div className="flex space-x-2">
                      <Button
                        onClick={handleOrgCancel}
                        variant="outline"
                        className="rounded-xl"
                        disabled={orgUpdating}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleOrgSave}
                        className="rounded-xl"
                        disabled={orgUpdating}
                      >
                        {orgUpdating ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Check className="w-4 h-4 mr-2" />
                        )}
                        Save
                      </Button>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Organization Logo */}
                  <div className="space-y-4">
                    <Label className="text-sm font-medium text-slate-700">Organization Logo</Label>
                    <div className="flex flex-col items-center space-y-4">
                      <div className="w-24 h-24 bg-slate-100 rounded-xl flex items-center justify-center overflow-hidden">
                        {logoPreview || organization.logo_url ? (
                          <img
                            src={logoPreview || organization.logo_url || ''}
                            alt="Organization Logo"
                            className="w-full h-full object-cover rounded-xl"
                          />
                        ) : (
                          <Building className="w-8 h-8 text-slate-500" />
                        )}
                      </div>
                      
                      <div className="flex space-x-2">
                        <input
                          id="orgLogo"
                          type="file"
                          accept="image/png,image/jpeg,image/jpg,image/webp"
                          onChange={handleLogoUpload}
                          className="hidden"
                        />
                        <Button
                          type="button"
                          onClick={() => document.getElementById('orgLogo')?.click()}
                          variant="outline"
                          className="rounded-xl"
                          size="sm"
                          disabled={isUploadingLogo}
                        >
                          {isUploadingLogo ? (
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          ) : (
                            <Upload className="w-4 h-4 mr-2" />
                          )}
                          {organization.logo_url ? 'Replace' : 'Upload'}
                        </Button>
                        
                        {organization.logo_url && (
                          <Button
                            type="button"
                            onClick={handleRemoveLogo}
                            variant="outline"
                            className="rounded-xl text-red-600 hover:text-red-700 hover:bg-red-50"
                            size="sm"
                            disabled={isUploadingLogo}
                          >
                            <X className="w-4 h-4 mr-2" />
                            Remove
                          </Button>
                        )}
                      </div>
                      
                      <p className="text-xs text-slate-500 text-center">
                        Max 5MB • PNG, JPEG, WEBP
                      </p>
                    </div>
                  </div>

                  {/* Organization Details */}
                  <div className="lg:col-span-2 space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label htmlFor="orgName" className="text-sm font-medium text-slate-700">
                          Organization Name
                        </Label>
                        {isEditingOrg ? (
                          <Input
                            id="orgName"
                            value={orgForm.name}
                            onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                            className="h-12 rounded-xl border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                            placeholder="Enter organization name"
                          />
                        ) : (
                          <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 text-slate-900 flex items-center">
                            {organization.name}
                          </div>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-slate-700">
                          Organization ID
                        </Label>
                        <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 text-slate-500 flex items-center font-mono text-sm">
                          {organization.id}
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-slate-700">
                          Created
                        </Label>
                        <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 text-slate-600 flex items-center">
                          {formatDate(organization.created_at)}
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-slate-700">
                          Last Updated
                        </Label>
                        <div className="h-12 px-3 py-2 border border-slate-200 rounded-xl bg-slate-50 text-slate-600 flex items-center">
                          {formatDate(organization.updated_at)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
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
            </>
          ) : (
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center">
              <Building className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-900 mb-2">No Organization Found</h3>
              <p className="text-slate-600">
                You don't have an organization yet. Contact your administrator to get added to an organization.
              </p>
            </div>
          )}
        </div>
      )}

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
                disabled={orgUpdating}
              >
                Cancel
              </Button>
              <Button
                onClick={handleDeleteOrg}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white rounded-xl"
                disabled={orgUpdating}
              >
                {orgUpdating ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : null}
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
