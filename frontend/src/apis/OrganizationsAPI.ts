// src/apis/OrganizationsAPI.ts
import { api } from "./configs/axiosConfig";
import { AxiosResponse } from "axios";

export type OrganizationDTO = {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
  created_at: string;
  updated_at: string;
};

export type UpdateOrganizationPayload = {
  name?: string;
  logo_url?: string;
};

export const OrganizationsAPI = {
  getUserOrganization: (): Promise<AxiosResponse<OrganizationDTO>> => 
    api.get<OrganizationDTO>("/user/organization/"),
  
  updateUserOrganization: (payload: UpdateOrganizationPayload): Promise<AxiosResponse<OrganizationDTO>> => 
    api.put<OrganizationDTO>("/user/organization/", payload),
};
