// src/apis/ChatAPI.ts
import { api } from "./configs/axiosConfig";
import { AxiosResponse } from "axios";

export type ChatMessage = {
  role: "user" | "assistant" | "system";
  content: string;
};

export type ChatCompletionPayload = {
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
};

export type ChatCompletionResponse = {
  id: string;
  choices: Array<{
    message: ChatMessage;
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model: string;
  created: number;
};

export type ChatStreamPayload = {
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
};

export const ChatAPI = {
  completions: (payload: ChatCompletionPayload): Promise<AxiosResponse<ChatCompletionResponse>> => 
    api.post<ChatCompletionResponse>("/chat/completions/", payload),
  
  stream: (payload: ChatStreamPayload): Promise<AxiosResponse<ReadableStream>> => 
    api.post<ReadableStream>("/chat/stream/", payload, {
      responseType: 'stream',
      headers: {
        'Accept': 'text/event-stream',
      },
    }),
};
