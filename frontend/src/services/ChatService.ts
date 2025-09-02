// src/services/ChatService.ts
import { ChatAPI, ChatMessage, ChatCompletionPayload, ChatStreamPayload } from "../apis/ChatAPI";

export type Message = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  error?: string;
};

export type ChatSession = {
  id: string;
  messages: Message[];
  created_at: Date;
  updated_at: Date;
};

export type StreamChunk = {
  id: string;
  content: string;
  finished: boolean;
};

export class ChatService {
  async sendMessage(
    messages: ChatMessage[],
    options?: {
      temperature?: number;
      max_tokens?: number;
    }
  ): Promise<Message> {
    const payload: ChatCompletionPayload = {
      messages,
      temperature: options?.temperature || 0.7,
      max_tokens: options?.max_tokens || 1000,
      stream: false,
    };

    const { data } = await ChatAPI.completions(payload);
    
    const assistantMessage = data.choices[0]?.message;
    if (!assistantMessage) {
      throw new Error("No response from chat API");
    }

    return {
      id: data.id,
      role: assistantMessage.role,
      content: assistantMessage.content,
      timestamp: new Date(data.created * 1000),
    };
  }

  async *streamMessage(
    messages: ChatMessage[],
    options?: {
      temperature?: number;
      max_tokens?: number;
    }
  ): AsyncGenerator<StreamChunk, void, unknown> {
    const payload: ChatStreamPayload = {
      messages,
      temperature: options?.temperature || 0.7,
      max_tokens: options?.max_tokens || 1000,
    };

    const response = await ChatAPI.stream(payload);
    const reader = response.data.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              yield { id: '', content: '', finished: true };
              return;
            }

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.delta?.content || '';
              if (content) {
                yield {
                  id: parsed.id,
                  content,
                  finished: false,
                };
              }
            } catch (error) {
              console.warn('Failed to parse SSE data:', error);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  createMessage(role: "user" | "assistant", content: string): Message {
    return {
      id: this.generateMessageId(),
      role,
      content,
      timestamp: new Date(),
    };
  }

  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Singleton instance for app-wide usage
export const chatService = new ChatService();
