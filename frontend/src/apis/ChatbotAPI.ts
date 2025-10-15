// src/apis/ChatbotAPI.ts
import { api } from "./configs/axiosConfig";
import { AxiosResponse } from "axios";

export type ChatbotTone = "friendly" | "technical" | "formal" | "professional";

export type DocumentInfo = {
  id: string;
  name: string;
  connected: boolean;
};

export type ChatbotConfigDTO = {
  id: string;
  name: string;
  tone: ChatbotTone;
  system_instructions: string;
  llm_provider: string | null;
  llm_model: string | null;
  llm_api_key_preview: string | null;
  llm_system_prompt: string;
  llm_is_active: boolean;
  documents_connected_ids: string[];
  documents_available: DocumentInfo[];
  created_at: string;
  updated_at: string;
};

export type UpdateChatbotPayload = {
  name?: string;
  tone?: ChatbotTone;
  system_instructions?: string;
  llm_provider?: string;
  llm_model?: string;
  llm_api_key?: string;
  llm_system_prompt?: string;
  llm_is_active?: boolean;
  documents_connected?: string[];
};

export type TestApiKeyPayload = {
  provider: string;
  model_name: string;
  api_key: string;
};

export type TestApiKeyResponse = {
  success: boolean;
  message: string;
  details: {
    model?: string;
    usage?: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
    response?: string;
  };
};

export type ChatMessage = {
  type: "user" | "bot";
  content: string;
  timestamp?: string;
};

export type SendMessagePayload = {
  message: string;
  history?: ChatMessage[];
};

export type SendMessageResponse = {
  reply: string;
  sources: string[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  latency_ms: number;
};

export const ChatbotAPI = {
  getConfig: (): Promise<AxiosResponse<ChatbotConfigDTO>> => 
    api.get<ChatbotConfigDTO>("/chatbot"),
  
  updateConfig: (payload: UpdateChatbotPayload): Promise<AxiosResponse<ChatbotConfigDTO>> => 
    api.put<ChatbotConfigDTO>("/chatbot", payload),
  
  testApiKey: (payload: TestApiKeyPayload): Promise<AxiosResponse<TestApiKeyResponse>> => 
    api.post<TestApiKeyResponse>("/chatbot/test-api-key", payload),
  
  sendMessage: (payload: SendMessagePayload): Promise<AxiosResponse<SendMessageResponse>> => 
    api.post<SendMessageResponse>("/chatbot/message", payload),
};
