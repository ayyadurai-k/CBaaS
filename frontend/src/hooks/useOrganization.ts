import { useState, useEffect } from 'react';
import { organizationsService, Organization } from '@/services/OrganizationsService';
import { UpdateOrganizationPayload } from '@/apis/OrganizationsAPI';
import { useAuth } from '@/hooks/redux/useAuth';
import { SessionCleanupService } from '@/services/auth/SessionCleanupService';
import { toast } from '@/hooks/use-toast';
import { useAppDispatch } from '@/store/hooks';
import { updateProfileField } from '@/store/slices/userSlice';

interface UseOrganizationReturn {
  organization: Organization | null;
  isLoading: boolean;
  isUpdating: boolean;
  isUploadingLogo: boolean;
  error: string | null;
  logoVersion: number;
  updateOrganization: (payload: UpdateOrganizationPayload) => Promise<boolean>;
  uploadOrganizationLogo: (file: File) => Promise<boolean>;
  deleteOrganizationLogo: () => Promise<boolean>;
  deleteOrganization: () => Promise<boolean>;
  refetchOrganization: () => Promise<void>;
}

export const useOrganization = (): UseOrganizationReturn => {
  const { logout } = useAuth();
  const dispatch = useAppDispatch();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logoVersion, setLogoVersion] = useState<number>(Date.now());

  const fetchOrganization = async () => {
    try {
      setError(null);
      const org = await organizationsService.getUserOrganization();
      setOrganization(org);
    } catch (err: any) {
      console.error('Failed to fetch organization:', err);
      if (err.response?.status === 404) {
        setError('No organization found');
      } else {
        setError('Failed to load organization data');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const updateOrganization = async (payload: UpdateOrganizationPayload): Promise<boolean> => {
    setIsUpdating(true);
    setError(null);
    
    try {
      const updatedOrg = await organizationsService.updateUserOrganization(payload);
      setOrganization(updatedOrg);
      
      // Update Redux store to keep user profile in sync
      dispatch(updateProfileField({ 
        organization: {
          id: updatedOrg.id,
          name: updatedOrg.name,
          slug: updatedOrg.slug,
          logo_url: updatedOrg.logo_url,
          created_at: updatedOrg.created_at,
          updated_at: updatedOrg.updated_at,
        }
      }));
      
      toast({
        title: "Organization updated",
        description: "Organization details have been updated successfully",
      });
      return true;
    } catch (err: any) {
      console.error('Failed to update organization:', err);
      
      let errorMessage = 'Failed to update organization';
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else {
          const errorMessages = Object.values(err.response.data).flat().join(', ');
          errorMessage = errorMessages || errorMessage;
        }
      }
      
      setError(errorMessage);
      toast({
        title: "Update failed",
        description: errorMessage,
        variant: "destructive",
      });
      return false;
    } finally {
      setIsUpdating(false);
    }
  };

  const uploadOrganizationLogo = async (file: File): Promise<boolean> => {
    setIsUploadingLogo(true);
    setError(null);
    
    try {
      const updatedOrg = await organizationsService.uploadOrganizationLogo(file);
      setOrganization(updatedOrg);
      setLogoVersion(Date.now()); // Update version to bust cache
      
      // Update Redux store to keep user profile in sync
      dispatch(updateProfileField({ 
        organization: {
          id: updatedOrg.id,
          name: updatedOrg.name,
          slug: updatedOrg.slug,
          logo_url: updatedOrg.logo_url,
          created_at: updatedOrg.created_at,
          updated_at: updatedOrg.updated_at,
        }
      }));
      
      toast({
        title: "Logo uploaded",
        description: "Organization logo has been updated successfully",
      });
      return true;
    } catch (err: any) {
      console.error('Failed to upload logo:', err);
      
      let errorMessage = 'Failed to upload logo';
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else {
          const errorMessages = Object.values(err.response.data).flat().join(', ');
          errorMessage = errorMessages || errorMessage;
        }
      }
      
      setError(errorMessage);
      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      });
      return false;
    } finally {
      setIsUploadingLogo(false);
    }
  };

  const deleteOrganizationLogo = async (): Promise<boolean> => {
    setIsUploadingLogo(true);
    setError(null);
    
    try {
      const updatedOrg = await organizationsService.deleteOrganizationLogo();
      setOrganization(updatedOrg);
      setLogoVersion(Date.now()); // Update version to bust cache
      
      // Update Redux store to keep user profile in sync
      dispatch(updateProfileField({ 
        organization: {
          id: updatedOrg.id,
          name: updatedOrg.name,
          slug: updatedOrg.slug,
          logo_url: updatedOrg.logo_url,
          created_at: updatedOrg.created_at,
          updated_at: updatedOrg.updated_at,
        }
      }));
      
      toast({
        title: "Logo removed",
        description: "Organization logo has been removed successfully",
      });
      return true;
    } catch (err: any) {
      console.error('Failed to delete logo:', err);
      
      let errorMessage = 'Failed to remove logo';
      if (err.response?.status === 404) {
        errorMessage = 'No logo to remove';
      } else if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else {
          const errorMessages = Object.values(err.response.data).flat().join(', ');
          errorMessage = errorMessages || errorMessage;
        }
      }
      
      setError(errorMessage);
      toast({
        title: "Failed to remove logo",
        description: errorMessage,
        variant: "destructive",
      });
      return false;
    } finally {
      setIsUploadingLogo(false);
    }
  };

  const deleteOrganization = async (): Promise<boolean> => {
    setIsUpdating(true);
    setError(null);
    
    try {
      await organizationsService.deleteOrganization();
      
      // Show success message immediately
      toast({
        title: "Organization deleted",
        description: "Your organization and all associated data have been permanently deleted. You will be logged out.",
        variant: "destructive",
      });
      
      // Clear local state
      setOrganization(null);
      
      // Perform complete session cleanup and redirect
      setTimeout(async () => {
        try {
          await logout();
          await SessionCleanupService.cleanupAfterOrganizationDeletion();
        } catch (cleanupError) {
          console.error('Error during cleanup after organization deletion:', cleanupError);
          // Force redirect even if cleanup fails
          window.location.href = '/login';
        }
      }, 2000); // Give user time to see the success message
      
      return true;
    } catch (err: any) {
      console.error('Failed to delete organization:', err);
      
      let errorMessage = 'Failed to delete organization';
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else if (err.response.data.detail) {
          errorMessage = err.response.data.detail;
        } else {
          const errorMessages = Object.values(err.response.data).flat().join(', ');
          errorMessage = errorMessages || errorMessage;
        }
      }
      
      setError(errorMessage);
      toast({
        title: "Deletion failed",
        description: errorMessage,
        variant: "destructive",
      });
      return false;
    } finally {
      setIsUpdating(false);
    }
  };

  const refetchOrganization = async () => {
    setIsLoading(true);
    await fetchOrganization();
  };

  useEffect(() => {
    fetchOrganization();
  }, []);

  return {
    organization,
    isLoading,
    isUpdating,
    isUploadingLogo,
    error,
    logoVersion,
    updateOrganization,
    uploadOrganizationLogo,
    deleteOrganizationLogo,
    deleteOrganization,
    refetchOrganization,
  };
};