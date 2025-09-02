// src/services/ChatbotService.ts
import { ChatbotAPI, ChatbotDTO, CreateChatbotPayload, UpdateChatbotPayload } from "../apis/ChatbotAPI";

export type Chatbot = {
  id: string;
  organization: string;
  name: string;
  tone: "Friendly" | "Technical" | "Formal";
  system_instructions: string;
  created_at: Date;
  updated_at: Date;
  is_configured: boolean;
};

export class ChatbotService {
  async get(): Promise<Chatbot | null> {
    try {
      const { data } = await ChatbotAPI.get();
      return this.normalizeChatbot(data);
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  async create(payload: CreateChatbotPayload): Promise<Chatbot> {
    const { data } = await ChatbotAPI.create(payload);
    return this.normalizeChatbot(data);
  }

  async update(payload: UpdateChatbotPayload): Promise<Chatbot> {
    const { data } = await ChatbotAPI.update(payload);
    return this.normalizeChatbot(data);
  }

  async delete(): Promise<void> {
    await ChatbotAPI.remove();
  }

  private normalizeChatbot(chatbot: ChatbotDTO): Chatbot {
    return {
      ...chatbot,
      created_at: new Date(chatbot.created_at),
      updated_at: new Date(chatbot.updated_at),
      is_configured: Boolean(chatbot.name && chatbot.system_instructions),
    };
  }
}

// Singleton instance for app-wide usage
export const chatbotService = new ChatbotService();
