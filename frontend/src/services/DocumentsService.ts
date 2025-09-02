// src/services/DocumentsService.ts
import { DocumentsAPI, DocumentDTO, DocumentUploadPayload } from "../apis/DocumentsAPI";

export type Document = {
  id: string;
  organization: string;
  name: string;
  file_type: "pdf" | "docx" | "txt" | "md" | "csv";
  size_bytes: number;
  upload_date: Date;
  status: "processing" | "ready" | "failed";
  url: string;
  size_formatted: string;
  is_processing: boolean;
  is_ready: boolean;
  is_failed: boolean;
};

export class DocumentsService {
  async list(): Promise<Document[]> {
    const { data } = await DocumentsAPI.getAll();
    return data.map(this.normalizeDocument);
  }

  async getById(id: string): Promise<Document> {
    const { data } = await DocumentsAPI.getById(id);
    return this.normalizeDocument(data);
  }

  async upload(payload: DocumentUploadPayload): Promise<Document> {
    const { data } = await DocumentsAPI.upload(payload);
    return this.normalizeDocument(data);
  }

  async reprocess(id: string): Promise<Document> {
    const { data } = await DocumentsAPI.reprocess(id);
    return this.normalizeDocument(data);
  }

  async delete(id: string): Promise<void> {
    await DocumentsAPI.remove(id);
  }

  private normalizeDocument(doc: DocumentDTO): Document {
    return {
      ...doc,
      upload_date: new Date(doc.upload_date),
      size_formatted: this.formatFileSize(doc.size_bytes),
      is_processing: doc.status === "processing",
      is_ready: doc.status === "ready",
      is_failed: doc.status === "failed",
    };
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }
}

// Singleton instance for app-wide usage
export const documentsService = new DocumentsService();
