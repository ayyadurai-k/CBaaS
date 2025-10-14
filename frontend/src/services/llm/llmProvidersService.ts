import LLMProvidersAPI, { LLMProvider, LLMProviderConfig, LLMModel } from '../../apis/llm/LLMProvidersAPI';

export class LLMProvidersService {
  /**
   * Get all active LLM providers with their models
   */
  async getProviders(): Promise<{ success: boolean; data?: LLMProvider[]; error?: string }> {
    try {
      const data = await LLMProvidersAPI.getProviders();
      return { success: true, data };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to fetch LLM providers'
      };
    }
  }

  /**
   * Get provider configuration in frontend-compatible format
   * This returns the same structure as the old hardcoded llmProviders object
   */
  async getProviderConfig(): Promise<{ success: boolean; data?: LLMProviderConfig; error?: string }> {
    try {
      const data = await LLMProvidersAPI.getProviderConfig();
      return { success: true, data };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to fetch provider configuration'
      };
    }
  }

  /**
   * Get models for a specific provider
   */
  async getProviderModels(providerName: string): Promise<{ success: boolean; data?: LLMModel[]; error?: string }> {
    try {
      const data = await LLMProvidersAPI.getProviderModels(providerName);
      return { success: true, data };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || `Failed to fetch models for ${providerName}`
      };
    }
  }

  /**
   * Get detailed information about a specific model
   */
  async getModelDetails(providerName: string, modelName: string): Promise<{ success: boolean; data?: LLMModel; error?: string }> {
    try {
      const data = await LLMProvidersAPI.getModelDetails(providerName, modelName);
      return { success: true, data };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || `Failed to fetch details for ${providerName}/${modelName}`
      };
    }
  }

  /**
   * Clear provider cache (admin only)
   */
  async clearCache(): Promise<{ success: boolean; error?: string }> {
    try {
      await LLMProvidersAPI.clearCache();
      return { success: true };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to clear provider cache'
      };
    }
  }
}

export const llmProvidersService = new LLMProvidersService();