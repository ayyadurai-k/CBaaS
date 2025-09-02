// src/apis/ChatbotProviderAPI.ts
import { api } from "./configs/axiosConfig";
import { AxiosResponse } from "axios";

export type ProviderType = "openai" | "gemini" | "deepseek";

export type ChatbotProviderDTO = {
  id: string;
  chatbot: string;
  provider: ProviderType;
  model_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type UpsertProviderPayload = {
  provider: ProviderType;
  model_name: string;
  api_key: string;
};

export type TestKeyPayload = {
  provider: ProviderType;
  api_key: string;
  model_name: string;
};

export type TestKeyResponse = {
  valid: boolean;
  message: string;
};

export const ChatbotProviderAPI = {
  get: (): Promise<AxiosResponse<ChatbotProviderDTO>> => 
    api.get<ChatbotProviderDTO>("/chatbot/provider/"),
  
  upsert: (payload: UpsertProviderPayload): Promise<AxiosResponse<ChatbotProviderDTO>> => 
    api.post<ChatbotProviderDTO>("/chatbot/provider/", payload),
  
  testKey: (payload: TestKeyPayload): Promise<AxiosResponse<TestKeyResponse>> => 
    api.post<TestKeyResponse>("/chatbot/test-key/", payload),
};
