// src/services/ChatbotProviderService.ts
import { ChatbotProviderAPI, ChatbotProviderDTO, UpsertProviderPayload, TestKeyPayload } from "../apis/ChatbotProviderAPI";

export type ChatbotProvider = {
  id: string;
  chatbot: string;
  provider: "openai" | "gemini" | "deepseek";
  model_name: string;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
  provider_display_name: string;
};

export class ChatbotProviderService {
  async get(): Promise<ChatbotProvider | null> {
    try {
      const { data } = await ChatbotProviderAPI.get();
      return this.normalizeProvider(data);
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  async upsert(payload: UpsertProviderPayload): Promise<ChatbotProvider> {
    const { data } = await ChatbotProviderAPI.upsert(payload);
    return this.normalizeProvider(data);
  }

  async testKey(payload: TestKeyPayload): Promise<{ valid: boolean; message: string }> {
    const { data } = await ChatbotProviderAPI.testKey(payload);
    return data;
  }

  getProviderDisplayName(provider: string): string {
    const names = {
      openai: "OpenAI",
      gemini: "Google Gemini",
      deepseek: "DeepSeek",
    };
    return names[provider as keyof typeof names] || provider;
  }

  getAvailableProviders() {
    return [
      { value: "openai", label: "OpenAI", models: ["gpt-4", "gpt-3.5-turbo"] },
      { value: "gemini", label: "Google Gemini", models: ["gemini-pro", "gemini-pro-vision"] },
      { value: "deepseek", label: "DeepSeek", models: ["deepseek-chat", "deepseek-coder"] },
    ];
  }

  private normalizeProvider(provider: ChatbotProviderDTO): ChatbotProvider {
    return {
      ...provider,
      created_at: new Date(provider.created_at),
      updated_at: new Date(provider.updated_at),
      provider_display_name: this.getProviderDisplayName(provider.provider),
    };
  }
}

// Singleton instance for app-wide usage
export const chatbotProviderService = new ChatbotProviderService();
