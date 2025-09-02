// src/services/ApiKeysService.ts
import { APIKeysAPI, APIKeyDTO, CreateAPIKeyPayload } from "../apis/ApiKeysAPI";

export type APIKey = {
  id: string;
  name: string;
  status: "active" | "revoked";
  usage_count: number;
  quota?: number;
  scope: "full-access" | "read-only" | "upload-only";
  created_at: Date;
  plaintext?: string;
};

export class ApiKeysService {
  async list(): Promise<APIKey[]> {
    const { data } = await APIKeysAPI.getAll();
    return data.map(this.normalizeAPIKey);
  }

  async create(payload: CreateAPIKeyPayload): Promise<APIKey> {
    const { data } = await APIKeysAPI.create(payload);
    return this.normalizeAPIKey(data);
  }

  async revoke(id: string): Promise<APIKey> {
    const { data } = await APIKeysAPI.revoke(id);
    return this.normalizeAPIKey(data);
  }

  async delete(id: string): Promise<void> {
    await APIKeysAPI.remove(id);
  }

  private normalizeAPIKey(apiKey: APIKeyDTO): APIKey {
    return {
      ...apiKey,
      created_at: new Date(apiKey.created_at),
    };
  }
}

// Singleton instance for app-wide usage
export const apiKeysService = new ApiKeysService();
