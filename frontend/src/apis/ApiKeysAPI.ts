// src/apis/ApiKeysAPI.ts
import { AxiosResponse } from "axios";
import { api } from "./configs/axiosConfig";

export type APIKeyStatus = "active" | "revoked";
export type APIKeyScope = "full-access" | "read-only" | "upload-only";

export type APIKeyDTO = {
  id: string;
  name: string;
  status: APIKeyStatus;
  usage_count: number;
  quota?: number;
  scope: APIKeyScope;
  created_at: string;
  plaintext?: string; // Only available when creating
};

export type CreateAPIKeyPayload = {
  name: string;
  quota?: number;
  scope: APIKeyScope;
};

export const APIKeysAPI = {
  getAll: (): Promise<AxiosResponse<APIKeyDTO[]>> => 
    api.get<APIKeyDTO[]>("/keys/"),
  
  create: (payload: CreateAPIKeyPayload): Promise<AxiosResponse<APIKeyDTO>> => 
    api.post<APIKeyDTO>("/keys/", payload),
  
  revoke: (id: string): Promise<AxiosResponse<APIKeyDTO>> => 
    api.post<APIKeyDTO>(`/keys/${id}/revoke/`, {}),
  
  remove: (id: string): Promise<AxiosResponse<void>> => 
    api.delete<void>(`/keys/${id}/`),
};
