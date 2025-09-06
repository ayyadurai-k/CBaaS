import { useState, useEffect } from 'react';
import { UsersAPI, UserDTO, UpdateProfilePayload } from '@/apis/UsersAPI';

interface UseProfileReturn {
  profile: UserDTO | null;
  isLoading: boolean;
  isUpdating: boolean;
  error: string | null;
  updateProfile: (payload: UpdateProfilePayload) => Promise<boolean>;
  refetchProfile: () => Promise<void>;
}

export const useProfile = (): UseProfileReturn => {
  const [profile, setProfile] = useState<UserDTO | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async () => {
    try {
      setError(null);
      const response = await UsersAPI.getProfile();
      setProfile(response.data);
    } catch (err: any) {
      console.error('Failed to fetch profile:', err);
      setError('Failed to load profile data');
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (payload: UpdateProfilePayload): Promise<boolean> => {
    setIsUpdating(true);
    setError(null);
    
    try {
      const response = await UsersAPI.updateProfile(payload);
      setProfile(response.data);
      return true;
    } catch (err: any) {
      console.error('Failed to update profile:', err);
      
      if (err.response?.data) {
        const errorMessages = Object.values(err.response.data).flat().join(', ');
        setError(errorMessages);
      } else {
        setError('Failed to update profile');
      }
      return false;
    } finally {
      setIsUpdating(false);
    }
  };

  const refetchProfile = async () => {
    setIsLoading(true);
    await fetchProfile();
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  return {
    profile,
    isLoading,
    isUpdating,
    error,
    updateProfile,
    refetchProfile,
  };
};
