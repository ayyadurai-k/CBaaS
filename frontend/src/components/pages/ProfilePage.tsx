import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ImageCropper } from "@/components/ui/image-cropper";
import { toast } from "@/hooks/use-toast";
import { useProfile } from "@/hooks/redux/useProfile";
import { UpdateProfilePayload } from "@/apis/UsersAPI";
import { getErrorMessage } from "@/apis/configs/axiosUtils";
import {
  User,
  Mail,
  Phone,
  Calendar,
  Building,
  Shield,
  Save,
  Loader2,
  Camera,
  Upload,
  X,
} from "lucide-react";

// Helper functions moved outside component to prevent re-declaration on each render
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
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

export const ProfilePage: React.FC = () => {
  const {
    profile,
    isLoading,
    isUpdating,
    isUploadingPicture,
    error,
    updateProfile,
    uploadProfilePicture,
    deleteProfilePicture,
    initials,
    avatarUrl,
  } = useProfile();
  const [isEditing, setIsEditing] = useState(false);
  const [showProfilePictureModal, setShowProfilePictureModal] = useState(false);
  const [showCropper, setShowCropper] = useState(false);
  const [selectedImageUrl, setSelectedImageUrl] = useState<string>("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [formData, setFormData] = useState({
    name: "",
    phone_number: "",
  });

  // Update form data when profile loads
  useEffect(() => {
    if (profile) {
      setFormData({
        name: profile.name || "",
        phone_number: profile.phone_number || "",
      });
    }
  }, [profile]);

  // Show error toast when error changes
  useEffect(() => {
    if (error) {
      toast({
        title: "Error",
        description: error,
        variant: "destructive",
      });
    }
  }, [error]);

  const handleInputChange = (
    field: keyof UpdateProfilePayload,
    value: string
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSave = async () => {
    if (!profile) return;

    const payload: UpdateProfilePayload = {};

    // Only include changed fields
    if (formData.name !== profile.name) {
      payload.name = formData.name;
    }
    if (formData.phone_number !== profile.phone_number) {
      payload.phone_number = formData.phone_number;
    }

    // If no changes, just exit edit mode
    if (Object.keys(payload).length === 0) {
      setIsEditing(false);
      return;
    }

    const success = await updateProfile(payload);
    if (success) {
      setIsEditing(false);
      toast({
        title: "Success",
        description: "Profile updated successfully",
      });
    }
  };

  const handleCancel = () => {
    if (!profile) return;

    // Reset form data to original values
    setFormData({
      name: profile.name || "",
      phone_number: profile.phone_number || "",
    });
    setIsEditing(false);
  };

  const handleFileSelect = (file: File) => {
    // Validate file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (file.size > maxSize) {
      toast({
        title: "File too large",
        description: "Image size must be less than 5MB",
        variant: "destructive",
      });
      return;
    }

    // Validate file type
    const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      toast({
        title: "Invalid file type",
        description: "Please select a JPEG, PNG, or WEBP image",
        variant: "destructive",
      });
      return;
    }

    // Create preview URL and show cropper
    const imageUrl = URL.createObjectURL(file);
    setSelectedImageUrl(imageUrl);
    setShowCropper(true);
  };

  const handleCropComplete = async (croppedImageBlob: Blob) => {
    setUploadProgress(0);

    // Create artificial delay with progress
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 15;
      });
    }, 200);

    // Convert blob to file
    const croppedFile = new File([croppedImageBlob], "profile-picture.jpg", {
      type: "image/jpeg",
    });

    try {
      const success = await uploadProfilePicture(croppedFile);

      // Complete progress
      clearInterval(progressInterval);
      setUploadProgress(100);

      if (success) {
        setTimeout(() => {
          setShowCropper(false);
          setShowProfilePictureModal(false);
          setUploadProgress(0);
          // Clean up the preview URL
          if (selectedImageUrl) {
            URL.revokeObjectURL(selectedImageUrl);
            setSelectedImageUrl("");
          }
          toast({
            title: "Success",
            description: "Profile picture updated successfully",
          });
        }, 500);
      } else {
        setUploadProgress(0);
        clearInterval(progressInterval);
      }
    } catch (error) {
      clearInterval(progressInterval);
      setUploadProgress(0);
      const errorMessage = getErrorMessage(error, 'Failed to upload profile picture');
      console.error("Error uploading profile picture:", error);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleCropCancel = () => {
    setShowCropper(false);
    // Clean up the preview URL
    if (selectedImageUrl) {
      URL.revokeObjectURL(selectedImageUrl);
      setSelectedImageUrl("");
    }
  };

  const handleProfilePictureUpload = async (file: File) => {
    handleFileSelect(file);
  };

  const handleProfilePictureDelete = async () => {
    const success = await deleteProfilePicture();
    if (success) {
      setShowProfilePictureModal(false);
      toast({
        title: "Success",
        description: "Profile picture removed successfully",
      });
    }
  };

  const handleModalClose = () => {
    setShowProfilePictureModal(false);
    setShowCropper(false);
    if (selectedImageUrl) {
      URL.revokeObjectURL(selectedImageUrl);
      setSelectedImageUrl("");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-2">
          <p className="text-lg font-medium text-slate-900">
            Profile not found
          </p>
          <p className="text-sm text-slate-600">Unable to load profile data</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Profile
          </h1>
          <p className="text-base text-slate-600">
            Manage your account settings and personal information.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          {isEditing ? (
            <>
              <Button
                variant="outline"
                onClick={handleCancel}
                disabled={isUpdating}
                className="px-5 py-3"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={isUpdating}
                className="px-5 py-3"
              >
                {isUpdating ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                Save Changes
              </Button>
            </>
          ) : (
            <Button onClick={() => setIsEditing(true)} className="px-5 py-3">
              <User className="w-4 h-4 mr-2" />
              Edit Profile
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Overview */}
        <Card className="border-slate-200 lg:col-span-1">
          <CardHeader className="text-center pb-4">
            <div className="relative w-24 h-24 mx-auto mb-4">
              <Avatar className="w-24 h-24">
                <AvatarImage
                  src={avatarUrl || ""}
                  alt={profile?.name || "User"}
                />
                <AvatarFallback className="text-xl font-semibold bg-slate-100 text-slate-700">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <button
                onClick={() => setShowProfilePictureModal(true)}
                className="absolute -bottom-1 -right-1 w-8 h-8 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center shadow-lg transition-colors"
                title="Change profile picture"
              >
                <Camera className="w-4 h-4" />
              </button>
            </div>
            <CardTitle className="text-xl text-slate-900">
              {profile.name}
            </CardTitle>
            <div className="flex justify-center">
              <Badge
                variant={getRoleBadgeVariant(profile.role)}
                className="capitalize"
              >
                <Shield className="w-3 h-3 mr-1" />
                {profile.role}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3 text-sm">
              <Mail className="w-4 h-4 text-slate-400" />
              <span className="text-slate-600">{profile.email}</span>
            </div>
            {profile.phone_number && (
              <div className="flex items-center gap-3 text-sm">
                <Phone className="w-4 h-4 text-slate-400" />
                <span className="text-slate-600">{profile.phone_number}</span>
              </div>
            )}
            <div className="flex items-center gap-3 text-sm">
              <Calendar className="w-4 h-4 text-slate-400" />
              <span className="text-slate-600">
                Joined {formatDate(profile.created_at)}
              </span>
            </div>
            {profile.organization && (
              <div className="flex items-center gap-3 text-sm">
                <Building className="w-4 h-4 text-slate-400" />
                <span className="text-slate-600">
                  {profile.organization.name}
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Profile Details */}
        <Card className="border-slate-200 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg text-slate-900">
              Personal Information
            </CardTitle>
            <p className="text-sm text-slate-600">
              Update your personal details and contact information.
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label
                  htmlFor="name"
                  className="text-sm font-medium text-slate-700"
                >
                  Full Name
                </Label>
                {isEditing ? (
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleInputChange("name", e.target.value)}
                    placeholder="Enter your full name"
                    className="border-slate-200"
                  />
                ) : (
                  <div className="px-3 py-2 border border-slate-200 rounded-md bg-slate-50 text-slate-900">
                    {profile.name}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="email"
                  className="text-sm font-medium text-slate-700"
                >
                  Email Address
                </Label>
                <div className="px-3 py-2 border border-slate-200 rounded-md bg-slate-50 text-slate-500">
                  {profile.email}
                  <p className="text-xs text-slate-400 mt-1">
                    Email cannot be changed
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="phone"
                  className="text-sm font-medium text-slate-700"
                >
                  Phone Number
                </Label>
                {isEditing ? (
                  <Input
                    id="phone"
                    value={formData.phone_number}
                    onChange={(e) =>
                      handleInputChange("phone_number", e.target.value)
                    }
                    placeholder="Enter your phone number"
                    className="border-slate-200"
                  />
                ) : (
                  <div className="px-3 py-2 border border-slate-200 rounded-md bg-slate-50 text-slate-900">
                    {profile.phone_number || "Not provided"}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="role"
                  className="text-sm font-medium text-slate-700"
                >
                  Role
                </Label>
                <div className="px-3 py-2 border border-slate-200 rounded-md bg-slate-50 text-slate-500 capitalize">
                  {profile.role}
                  <p className="text-xs text-slate-400 mt-1">
                    Role is managed by organization
                  </p>
                </div>
              </div>
            </div>

            <Separator className="my-6" />

            <div className="space-y-4">
              <h3 className="text-sm font-medium text-slate-900">
                Account Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">
                    Member Since
                  </Label>
                  <div className="px-3 py-2 border border-slate-200 rounded-md bg-slate-50 text-slate-600">
                    {formatDate(profile.created_at)}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">
                    Last Updated
                  </Label>
                  <div className="px-3 py-2 border border-slate-200 rounded-md bg-slate-50 text-slate-600">
                    {formatDate(profile.updated_at)}
                  </div>
                </div>
              </div>
            </div>

            {profile.organization && (
              <>
                <Separator className="my-6" />
                <div className="space-y-4">
                  <h3 className="text-sm font-medium text-slate-900">
                    Organization
                  </h3>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-slate-700">
                      Organization Name
                    </Label>
                    <div className="px-3 py-2 border border-slate-200 rounded-md bg-slate-50 text-slate-600">
                      {profile.organization.name}
                    </div>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Profile Picture Upload Modal */}
      {showProfilePictureModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-slate-900">
                Profile Picture
              </h3>
              <button
                onClick={handleModalClose}
                className="text-slate-500 hover:text-slate-700"
                disabled={isUploadingPicture}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {showCropper ? (
              <ImageCropper
                src={selectedImageUrl}
                onCropComplete={handleCropComplete}
                onCancel={handleCropCancel}
                isUploading={isUploadingPicture}
                uploadProgress={uploadProgress}
              />
            ) : (
              <div className="space-y-6">
                {/* Current Profile Picture */}
                <div className="text-center">
                  <Avatar className="w-32 h-32 mx-auto mb-4">
                    <AvatarImage src={avatarUrl || ""} alt={profile.name} />
                    <AvatarFallback className="text-2xl font-semibold bg-slate-100 text-slate-700">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                </div>

                {/* Upload Options */}
                <div className="space-y-4">
                  <div className="flex flex-col space-y-3">
                    <input
                      id="profile-picture-upload"
                      type="file"
                      accept="image/jpeg,image/jpg,image/png,image/webp"
                      onChange={(e) =>
                        e.target.files?.[0] &&
                        handleProfilePictureUpload(e.target.files[0])
                      }
                      className="hidden"
                    />
                    <Button
                      onClick={() =>
                        document
                          .getElementById("profile-picture-upload")
                          ?.click()
                      }
                      disabled={isUploadingPicture}
                      className="w-full rounded-xl"
                    >
                      {isUploadingPicture ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Upload className="w-4 h-4 mr-2" />
                      )}
                      {profile.profile_picture_url
                        ? "Change Picture"
                        : "Upload Picture"}
                    </Button>

                    {profile.profile_picture_url && (
                      <Button
                        onClick={handleProfilePictureDelete}
                        disabled={isUploadingPicture}
                        variant="outline"
                        className="w-full rounded-xl text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        {isUploadingPicture ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <X className="w-4 h-4 mr-2" />
                        )}
                        Remove Picture
                      </Button>
                    )}
                  </div>

                  <p className="text-xs text-slate-500 text-center">
                    Supports JPEG, PNG, WEBP • Max 5MB
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
