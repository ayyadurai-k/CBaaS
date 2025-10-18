// src/apis/ApiKeysAPI.ts
import { AxiosResponse } from "axios";
import { api } from "./configs/axiosConfig";

export type APIKeyStatus = "active" | "revoked" | "expired";
export type APIKeyScope = "full-access" | "read-only" | "upload-only";

export type APIKeyDTO = {
  id: string;
  name: string;
  status: APIKeyStatus;
  usage_count: number;
  quota?: number;
  scope: APIKeyScope;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
  expires_at?: string;
  allowed_ips: string[];
  rate_limit_per_minute?: number;
  metadata: Record<string, any>;
  revoked_reason: string;
  api_key?: string; // Only available when creating (plaintext field)
};

export type CreateAPIKeyPayload = {
  name: string;
  quota?: number;
  scope: APIKeyScope;
  expires_at?: string;
  allowed_ips?: string[];
  rate_limit_per_minute?: number;
  metadata?: Record<string, any>;
};

export type APIKeysPaginatedResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: APIKeyDTO[];
};

export const APIKeysAPI = {
  getAll: (params?: { page?: number; page_size?: number }): Promise<AxiosResponse<APIKeysPaginatedResponse>> => 
    api.get<APIKeysPaginatedResponse>("/keys/", { params }),
  
  create: (payload: CreateAPIKeyPayload): Promise<AxiosResponse<APIKeyDTO>> => 
    api.post<APIKeyDTO>("/keys/", payload),
  
  revoke: (id: string): Promise<AxiosResponse<void>> => 
    api.patch<void>(`/keys/${id}/revoke/`, {}),
  
  remove: (id: string): Promise<AxiosResponse<void>> => 
    api.delete<void>(`/keys/${id}/`),
};
