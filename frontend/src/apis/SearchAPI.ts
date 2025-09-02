// src/apis/search/SearchAPI.ts
import { api } from "../../lib/api";
import { AxiosResponse } from "axios";

export type SearchPayload = {
  query: string;
  limit?: number;
  threshold?: number;
};

export type SearchResult = {
  id: string;
  document_id: string;
  document_name: string;
  content: string;
  similarity_score: number;
  page_number?: number;
};

export type SearchResponse = {
  results: SearchResult[];
  query: string;
  total_results: number;
  execution_time_ms: number;
};

export const SearchAPI = {
  search: (payload: SearchPayload): Promise<AxiosResponse<SearchResponse>> => 
    api.post<SearchResponse>("/search/", payload),
};
