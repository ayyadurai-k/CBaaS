// src/apis/documents/DocumentsAPI.ts
import { api } from "../../lib/api";
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

export const DocumentsAPI = {
  getAll: (): Promise<AxiosResponse<DocumentDTO[]>> => 
    api.get<DocumentDTO[]>("/documents/"),
  
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
  
  reprocess: (id: string): Promise<AxiosResponse<DocumentDTO>> => 
    api.post<DocumentDTO>(`/documents/${id}/reprocess/`, {}),
  
  remove: (id: string): Promise<AxiosResponse<void>> => 
    api.delete<void>(`/documents/${id}/`),
};
