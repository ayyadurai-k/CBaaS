import { useState, useEffect } from 'react';
import { organizationsService, Organization } from '@/services/OrganizationsService';
import { UpdateOrganizationPayload } from '@/apis/OrganizationsAPI';
import { toast } from '@/hooks/use-toast';

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
      setOrganization(null);
      toast({
        title: "Organization deleted",
        description: "Your organization has been permanently deleted",
        variant: "destructive",
      });
      return true;
    } catch (err: any) {
      console.error('Failed to delete organization:', err);
      
      let errorMessage = 'Failed to delete organization';
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