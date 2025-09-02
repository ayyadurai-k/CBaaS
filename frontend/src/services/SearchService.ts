// src/services/SearchService.ts
import { SearchAPI, SearchPayload, SearchResponse } from "../apis/SearchAPI";

export type SearchResult = {
  id: string;
  document_id: string;
  document_name: string;
  content: string;
  similarity_score: number;
  page_number?: number;
  similarity_percentage: string;
  content_preview: string;
};

export type SearchResults = {
  results: SearchResult[];
  query: string;
  total_results: number;
  execution_time_ms: number;
  execution_time_formatted: string;
  has_results: boolean;
};

export class SearchService {
  async search(query: string, options?: { limit?: number; threshold?: number }): Promise<SearchResults> {
    const payload: SearchPayload = {
      query: query.trim(),
      limit: options?.limit || 10,
      threshold: options?.threshold || 0.7,
    };

    const { data } = await SearchAPI.search(payload);
    return this.normalizeSearchResults(data);
  }

  private normalizeSearchResults(response: SearchResponse): SearchResults {
    return {
      ...response,
      results: response.results.map(this.normalizeSearchResult),
      execution_time_formatted: `${response.execution_time_ms}ms`,
      has_results: response.results.length > 0,
    };
  }

  private normalizeSearchResult(result: SearchResult): SearchResult {
    return {
      ...result,
      similarity_percentage: `${Math.round(result.similarity_score * 100)}%`,
      content_preview: this.truncateContent(result.content, 200),
    };
  }

  private truncateContent(content: string, maxLength: number): string {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + "...";
  }
}

// Singleton instance for app-wide usage
export const searchService = new SearchService();
