// src/apis/DocumentsAPI.ts
import { api } from "./configs/axiosConfig";
import { AxiosResponse } from "axios";

export type DocumentFileType = "pdf" | "docx" | "txt" | "md" | "csv";
export type DocumentStatus = "processing" | "ready" | "failed";

export type DocumentDTO = {
  id: string;
  organization: string;
  name: string;
  file_type: DocumentFileType;
  size_bytes: number;
  upload_date: string;
  status: DocumentStatus;
  url: string;
};

export type DocumentUploadPayload = {
  name: string;
  file: File;
};

export type DocumentUpdatePayload = {
  name: string;
};

export type DocumentsPaginatedResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: DocumentDTO[];
};

export const DocumentsAPI = {
  getAll: (params?: { page?: number; page_size?: number }): Promise<AxiosResponse<DocumentsPaginatedResponse>> => 
    api.get<DocumentsPaginatedResponse>("/documents/", { params }),
  
  getById: (id: string): Promise<AxiosResponse<DocumentDTO>> => 
    api.get<DocumentDTO>(`/documents/${id}/`),
  
  upload: (payload: DocumentUploadPayload): Promise<AxiosResponse<DocumentDTO>> => {
    const formData = new FormData();
    formData.append('name', payload.name);
    formData.append('file', payload.file);
    
    return api.post<DocumentDTO>("/documents/", formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  update: (id: string, payload: DocumentUpdatePayload): Promise<AxiosResponse<DocumentDTO>> =>
    api.patch<DocumentDTO>(`/documents/${id}/`, payload),
  
  reprocess: (id: string): Promise<AxiosResponse<void>> => 
    api.post<void>(`/documents/${id}/reprocess/`, {}),
  
  remove: (id: string): Promise<AxiosResponse<void>> => 
    api.delete<void>(`/documents/${id}/`),
  
  download: (document: DocumentDTO): Promise<AxiosResponse<Blob>> => {
    // Use the dedicated download endpoint
    return api.get<Blob>(`/documents/${document.id}/download/`, {
      responseType: 'blob',
    });
  },
};
