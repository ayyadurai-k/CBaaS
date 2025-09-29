// src/apis/OrganizationsAPI.ts
import { api } from "./configs/axiosConfig";
import { AxiosResponse } from "axios";

export type OrganizationDTO = {
  id: string;
  name: string;
  slug: string;
  logo_url?: string | null;
  created_at: string;
  updated_at: string;
};

export type UpdateOrganizationPayload = {
  name?: string;
};

export const OrganizationsAPI = {
  getUserOrganization: (): Promise<AxiosResponse<OrganizationDTO>> => 
    api.get<OrganizationDTO>("/user/organization"),
  
  updateUserOrganization: (payload: UpdateOrganizationPayload): Promise<AxiosResponse<OrganizationDTO>> => 
    api.put<OrganizationDTO>("/user/organization", payload),

  uploadOrganizationLogo: (file: File): Promise<AxiosResponse<OrganizationDTO>> => {
    const formData = new FormData();
    formData.append('logo', file);
    return api.post<OrganizationDTO>("/user/organization/logo", formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  deleteOrganizationLogo: (): Promise<AxiosResponse<OrganizationDTO>> =>
    api.delete<OrganizationDTO>("/user/organization/logo"),

  deleteOrganization: (): Promise<AxiosResponse<void>> =>
    api.delete<void>("/user/organization"),
};
