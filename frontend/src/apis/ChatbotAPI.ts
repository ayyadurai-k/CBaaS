// src/apis/chatbot/ChatbotAPI.ts
import { api } from "../../lib/api";
import { AxiosResponse } from "axios";

export type ChatbotTone = "Friendly" | "Technical" | "Formal";

export type ChatbotDTO = {
  id: string;
  organization: string;
  name: string;
  tone: ChatbotTone;
  system_instructions: string;
  created_at: string;
  updated_at: string;
};

export type CreateChatbotPayload = {
  name: string;
  tone: ChatbotTone;
  system_instructions: string;
};

export type UpdateChatbotPayload = {
  name?: string;
  tone?: ChatbotTone;
  system_instructions?: string;
};

export const ChatbotAPI = {
  get: (): Promise<AxiosResponse<ChatbotDTO>> => 
    api.get<ChatbotDTO>("/chatbot/"),
  
  create: (payload: CreateChatbotPayload): Promise<AxiosResponse<ChatbotDTO>> => 
    api.post<ChatbotDTO>("/chatbot/", payload),
  
  update: (payload: UpdateChatbotPayload): Promise<AxiosResponse<ChatbotDTO>> => 
    api.put<ChatbotDTO>("/chatbot/", payload),
  
  remove: (): Promise<AxiosResponse<void>> => 
    api.delete<void>("/chatbot/"),
};
