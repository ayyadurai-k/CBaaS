import { api } from '../configs/axiosConfig';
import { AxiosResponse } from 'axios';

// Types for LLM providers and models
export interface LLMModel {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  context_window?: number;
  max_tokens?: number;
  supports_streaming: boolean;
  supports_function_calling: boolean;
  cost_per_1k_input_tokens?: number;
  cost_per_1k_output_tokens?: number;
  is_default: boolean;
  full_name: string;
}

export interface LLMProvider {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  api_base_url?: string;
  models: LLMModel[];
  active_models: LLMModel[];
}

export interface LLMProviderConfig {
  [key: string]: {
    name: string;
    models: string[];
    description?: string;
    api_base_url?: string;
  };
}

class LLMProvidersAPI {
  private baseURL = '/providers';

  /**
   * Get all active LLM providers with their models
   */
  async getProviders(): Promise<LLMProvider[]> {
    const response: AxiosResponse<LLMProvider[]> = await api.get(`${this.baseURL}/`);
    return response.data;
  }

  /**
   * Get simple list of providers (for dropdowns)
   */
  async getProvidersSimple(): Promise<Array<{ id: string; name: string; display_name: string }>> {
    const response: AxiosResponse<Array<{ id: string; name: string; display_name: string }>> = 
      await api.get(`${this.baseURL}/simple/`);
    return response.data;
  }

  /**
   * Get models for a specific provider
   */
  async getProviderModels(providerName: string): Promise<LLMModel[]> {
    const response: AxiosResponse<LLMModel[]> = await api.get(`${this.baseURL}/${providerName}/models/`);
    return response.data;
  }

  /**
   * Get provider configuration in frontend-compatible format
   * This matches the old hardcoded llmProviders object structure
   */
  async getProviderConfig(): Promise<LLMProviderConfig> {
    const response: AxiosResponse<LLMProviderConfig> = await api.get(`${this.baseURL}/config/`);
    return response.data;
  }

  /**
   * Get detailed information about a specific model
   */
  async getModelDetails(providerName: string, modelName: string): Promise<LLMModel> {
    const response: AxiosResponse<LLMModel> = await api.get(`${this.baseURL}/${providerName}/models/${modelName}/`);
    return response.data;
  }

  /**
   * Clear provider cache (admin only)
   */
  async clearCache(): Promise<void> {
    await api.post(`${this.baseURL}/cache/clear/`);
  }
}

export default new LLMProvidersAPI();