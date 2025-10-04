// src/apis/UsersAPI.ts
import { api } from "./configs/axiosConfig";
import { AxiosResponse } from "axios";

export type OrganizationDTO = {
  id: string;
  name: string;
  slug: string;
  logo_url: string | null;
  created_at: string;
  updated_at: string;
};

export type UserDTO = {
  id: string;
  email: string;
  name: string;
  role: string;
  phone_number?: string;
  created_at: string;
  updated_at: string;
  organization: OrganizationDTO | null;
  profile_picture_url?: string | null;
};

export type UpdateProfilePayload = {
  name?: string;
  phone_number?: string;
};

export const UsersAPI = {
  getProfile: (): Promise<AxiosResponse<UserDTO>> => 
    api.get<UserDTO>("/user/profile"),
  
  updateProfile: (payload: UpdateProfilePayload): Promise<AxiosResponse<UserDTO>> => 
    api.put<UserDTO>("/user/profile", payload),

  uploadProfilePicture: (file: File): Promise<AxiosResponse<UserDTO>> => {
    const formData = new FormData();
    formData.append('profile_picture', file);
    
    return api.post<UserDTO>("/user/profile/picture", formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  deleteProfilePicture: (): Promise<AxiosResponse<UserDTO>> => 
    api.delete<UserDTO>("/user/profile/picture"),
};
