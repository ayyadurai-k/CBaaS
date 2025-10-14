// src/services/ChatbotService.ts
import { 
  ChatbotAPI, 
  ChatbotConfigDTO, 
  UpdateChatbotPayload,
  TestApiKeyPayload,
  SendMessagePayload,
  DocumentInfo,
  ChatbotTone
} from "../apis/ChatbotAPI";

export type ChatbotConfig = {
  id: string;
  name: string;
  tone: ChatbotTone;
  system_instructions: string;
  llm_provider: string | null;
  llm_model: string | null;
  llm_system_prompt: string;
  llm_is_active: boolean;
  documents_connected_ids: string[];
  documents_available: DocumentInfo[];
  created_at: Date;
  updated_at: Date;
  is_fully_configured: boolean;
};

export type TestApiKeyResult = {
  success: boolean;
  message: string;
  details?: {
    model?: string;
    usage?: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
    response?: string;
  };
};

export type ChatMessageData = {
  type: "user" | "bot";
  content: string;
  timestamp?: string;
};

export type SendMessageResult = {
  reply: string;
  sources: string[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  latency_ms: number;
};

export class ChatbotService {
  /**
   * Get chatbot configuration including connected documents
   */
  async getConfig(): Promise<ChatbotConfig | null> {
    try {
      const { data } = await ChatbotAPI.getConfig();
      return this.normalizeConfig(data);
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw this.handleError(error);
    }
  }

  /**
   * Update chatbot configuration
   */
  async updateConfig(payload: UpdateChatbotPayload): Promise<ChatbotConfig> {
    try {
      const { data } = await ChatbotAPI.updateConfig(payload);
      return this.normalizeConfig(data);
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  /**
   * Test LLM provider API key
   */
  async testApiKey(payload: TestApiKeyPayload): Promise<TestApiKeyResult> {
    try {
      const { data } = await ChatbotAPI.testApiKey(payload);
      return {
        success: data.success,
        message: data.message,
        details: data.details,
      };
    } catch (error: any) {
      // API returns 400 for invalid keys with structured error
      if (error.response?.status === 400 && error.response?.data) {
        return {
          success: false,
          message: error.response.data.message || "API key test failed",
          details: error.response.data.details,
        };
      }
      throw this.handleError(error);
    }
  }

  /**
   * Send a message to the chatbot
   */
  async sendMessage(payload: SendMessagePayload): Promise<SendMessageResult> {
    try {
      const { data } = await ChatbotAPI.sendMessage(payload);
      return data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  /**
   * Normalize backend DTO to frontend model
   */
  private normalizeConfig(config: ChatbotConfigDTO): ChatbotConfig {
    return {
      ...config,
      created_at: new Date(config.created_at),
      updated_at: new Date(config.updated_at),
      is_fully_configured: Boolean(
        config.name && 
        config.llm_provider && 
        config.llm_model &&
        config.llm_is_active
      ),
    };
  }

  /**
   * Handle API errors with user-friendly messages
   */
  private handleError(error: any): Error {
    if (error.response?.data?.error) {
      return new Error(error.response.data.error);
    }
    if (error.response?.data?.detail) {
      return new Error(error.response.data.detail);
    }
    if (error.message) {
      return new Error(error.message);
    }
    return new Error("An unexpected error occurred");
  }
}

// Singleton instance for app-wide usage
export const chatbotService = new ChatbotService();
