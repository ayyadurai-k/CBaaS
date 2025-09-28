import React, { useState, useEffect } from "react";
import {
  Upload,
  FileText,
  Trash2,
  Download,
  Clock,
  CheckCircle,
  AlertCircle,
  X,
  Edit2,
  Check,
  Loader2,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";
import {
  DocumentsAPI,
  DocumentDTO,
  DocumentUploadPayload,
  DocumentUpdatePayload,
} from "@/apis/DocumentsAPI";
import {
  TablePagination,
  PaginationData,
} from "@/components/ui/table-pagination";

interface Document extends DocumentDTO {}


interface ConfirmModalData {
  show: boolean;
  type: "delete";
  documentId: string;
  documentName: string;
}

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentName, setDocumentName] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [editingDocId, setEditingDocId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [confirmModal, setConfirmModal] = useState<ConfirmModalData>({
    show: false,
    type: "delete",
    documentId: "",
    documentName: "",
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [paginationData, setPaginationData] = useState<PaginationData>({
    count: 0,
    next: null,
    previous: null,
    results: [],
  });

  // Polling state
  const [isPolling, setIsPolling] = useState(false);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(
    null
  );

  // Load documents from backend
  useEffect(() => {
    loadDocuments();
  }, []);

  // Cleanup polling interval on component unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Auto-start polling when there are processing documents
  useEffect(() => {
    const hasProcessingDocs = documents.some(
      (doc) => doc.status === "processing"
    );

    if (hasProcessingDocs && !isPolling && !pollingInterval) {
      startPolling();
    } else if (!hasProcessingDocs && pollingInterval) {
      stopPolling();
    }
  }, [documents, isPolling, pollingInterval]);

  const loadDocuments = async (page: number = 1, silent: boolean = false) => {
    try {
      if (!silent) {
        setLoading(true);
      }
      const response = await DocumentsAPI.getAll({ page });

      const responseData = response.data;
      let newDocuments: DocumentDTO[] = [];

      if (
        responseData &&
        typeof responseData === "object" &&
        "results" in responseData
      ) {
        // Paginated response
        newDocuments = responseData.results;
        setPaginationData(responseData);
        setCurrentPage(page);
      } else if (Array.isArray(responseData)) {
        // Direct array response (fallback)
        newDocuments = responseData as DocumentDTO[];
        setPaginationData({
          count: newDocuments.length,
          next: null,
          previous: null,
          results: newDocuments,
        });
      }

      // Check for status changes if this is a polling request
      if (silent && documents.length > 0) {
        checkForStatusChanges(documents, newDocuments);
      }

      setDocuments(newDocuments);
    } catch (error) {
      console.error("Failed to load documents:", error);

      // Only show error toast if it's not a silent polling request
      if (!silent) {
        setDocuments([]);
        setPaginationData({
          count: 0,
          next: null,
          previous: null,
          results: [],
        });
        toast({
          title: "Error",
          description: "Failed to load documents. Please try again.",
          variant: "destructive",
        });
      }
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  const checkForStatusChanges = (oldDocs: Document[], newDocs: Document[]) => {
    const docMap = new Map(oldDocs.map((doc) => [doc.id, doc]));

    newDocs.forEach((newDoc) => {
      const oldDoc = docMap.get(newDoc.id);
      if (oldDoc && oldDoc.status !== newDoc.status) {
        // Status changed
        if (newDoc.status === "ready") {
          toast({
            title: "Document ready",
            description: `${newDoc.name} has been processed successfully`,
          });
        } else if (newDoc.status === "failed") {
          toast({
            title: "Processing failed",
            description: `Failed to process ${newDoc.name}. You can try reprocessing it.`,
            variant: "destructive",
          });
        } else if (newDoc.status === "processing" && oldDoc.status === "failed") {
          toast({
            title: "Reprocessing started",
            description: `${newDoc.name} is being reprocessed`,
          });
        }
      }
    });
  };

  const startPolling = () => {
    if (pollingInterval) return; // Already polling

    console.log("Starting document polling...");
    setIsPolling(true);

    const interval = setInterval(async () => {
      console.log("Polling documents...");
      await loadDocuments(currentPage, true); // Silent reload
    }, 3000); // Poll every 3 seconds

    setPollingInterval(interval);
  };

  const stopPolling = () => {
    console.log("Stopping document polling...");
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
    setIsPolling(false);
  };

  const handlePageChange = (newPage: number) => {
    loadDocuments(newPage);
  };

  const getStatusIcon = (status: Document["status"]) => {
    switch (status) {
      case "ready":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "processing":
        return (
          <div className="flex items-center">
            <Clock className="w-5 h-5 text-yellow-500" />
            <div className="ml-1 w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
          </div>
        );
      case "failed":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: Document["status"]) => {
    switch (status) {
      case "ready":
        return "Ready";
      case "processing":
        return "Processing";
      case "failed":
        return "Failed";
      default:
        return "";
    }
  };

  const handleDelete = async (id: string) => {
    try {
      setIsSubmitting(true);
      await DocumentsAPI.remove(id);

      toast({
        title: "Document deleted",
        description: "The document has been removed from your knowledge base",
      });

      // If we deleted the last item on current page, go to previous page
      if (documents.length === 1 && currentPage > 1) {
        await loadDocuments(currentPage - 1);
      } else {
        await loadDocuments(currentPage);
      }
    } catch (error) {
      console.error("Failed to delete document:", error);
      toast({
        title: "Error",
        description: "Failed to delete document. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
      setConfirmModal({
        show: false,
        type: "delete",
        documentId: "",
        documentName: "",
      });
    }
  };

  const handleEditStart = (doc: Document) => {
    setEditingDocId(doc.id);
    setEditName(doc.name);
  };

  const handleEditSave = async (docId: string) => {
    if (!editName.trim()) {
      toast({
        title: "Error",
        description: "Document name cannot be empty",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSubmitting(true);
      const updatePayload: DocumentUpdatePayload = {
        name: editName.trim(),
      };

      await DocumentsAPI.update(docId, updatePayload);

      setEditingDocId(null);
      setEditName("");

      toast({
        title: "Document renamed",
        description: "The document name has been updated successfully",
      });

      // Reload the documents to get the updated data
      await loadDocuments(currentPage);
    } catch (error) {
      console.error("Failed to update document:", error);
      toast({
        title: "Error",
        description: "Failed to update document name. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditCancel = () => {
    setEditingDocId(null);
    setEditName("");
  };

  const handleDownload = async (doc: Document) => {
    try {
      const response = await DocumentsAPI.download(doc);

      // Handle different response types
      if (response.data instanceof Blob) {
        // Direct blob download
        const blob = response.data;
        const url = window.URL.createObjectURL(blob);
        const link = window.document.createElement("a");
        link.href = url;

        // Try to get filename from Content-Disposition header or use document name
        let filename = doc.name;
        const contentDisposition = response.headers["content-disposition"];
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(
            /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
          );
          if (filenameMatch) {
            filename = filenameMatch[1].replace(/['"]/g, "");
            // Decode if URL encoded
            try {
              filename = decodeURIComponent(filename);
            } catch (e) {
              // Keep original if decode fails
            }
          }
        }

        // Ensure filename has proper extension
        if (!filename.includes(".") && doc.file_type) {
          filename = `${filename}.${doc.file_type.toLowerCase()}`;
        }

        link.setAttribute("download", filename);
        window.document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);

        toast({
          title: "Download completed",
          description: `${filename} has been downloaded successfully`,
        });
      } else {
        // Handle JSON response with external URL
        const data = response.data as any;
        if (data.download_url) {
          window.open(data.download_url, "_blank");
          toast({
            title: "Opening document",
            description: data.message || "Document opened in new tab",
          });
        } else {
          throw new Error("Unexpected response format");
        }
      }
    } catch (error: any) {
      console.error("Failed to download document:", error);

      // Check if it's a 409 conflict (document not ready)
      if (error.response?.status === 409) {
        const errorData = error.response.data;
        toast({
          title: "Document not ready",
          description: `Document is currently ${errorData.status}. Please wait for processing to complete.`,
          variant: "destructive",
        });
      } else {
        // Fallback to direct URL if available
        if (doc.url) {
          window.open(doc.url, "_blank");
          toast({
            title: "Opening document",
            description: "Document opened in new tab",
          });
        } else {
          toast({
            title: "Download failed",
            description: "Failed to download document. Please try again later.",
            variant: "destructive",
          });
        }
      }
    }
  };

  const handleReprocess = async (doc: Document) => {
    try {
      setIsSubmitting(true);
      
      await DocumentsAPI.reprocess(doc.id);
      
      toast({
        title: "Reprocessing started",
        description: `${doc.name} is being reprocessed. This may take a few moments.`,
      });
      
      // Start polling since we now have a processing document
      if (!isPolling) {
        startPolling();
      }
      
      // Reload documents to show updated status
      await loadDocuments(currentPage, true);
      
    } catch (error: any) {
      console.error("Failed to reprocess document:", error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          "Failed to reprocess document. Please try again.";
      
      toast({
        title: "Reprocessing failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileSelect = (file: File) => {
    // Validate file type
    const allowedTypes = [".pdf", ".docx", ".txt", ".md", ".csv"];
    const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();

    if (!allowedTypes.includes(fileExtension)) {
      toast({
        title: "Invalid file type",
        description: "Please select a PDF, DOCX, TXT, MD, or CSV file",
        variant: "destructive",
      });
      return;
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      toast({
        title: "File too large",
        description: "File size must be less than 10MB",
        variant: "destructive",
      });
      return;
    }

    setSelectedFile(file);
    setDocumentName(file.name.split(".")[0]);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    if (!documentName.trim()) {
      toast({
        title: "Document name required",
        description: "Please enter a name for your document",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const uploadPayload: DocumentUploadPayload = {
        name: documentName.trim(),
        file: selectedFile,
      };

      // Simulate progress for user feedback
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await DocumentsAPI.upload(uploadPayload);
      clearInterval(progressInterval);
      setUploadProgress(100);

      setShowUploadModal(false);
      setSelectedFile(null);
      setDocumentName("");
      setUploadProgress(0);
      setIsUploading(false);

      toast({
        title: "Document uploaded successfully",
        description:
          "Your document is being processed and will be ready shortly",
      });

      // Go to first page to see the new document and start polling
      await loadDocuments(1);

      // Force start polling since we just uploaded a document that will be processing
      if (!isPolling) {
        startPolling();
      }
    } catch (error: any) {
      console.error("Failed to upload document:", error);
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.name?.[0] ||
        error.response?.data?.file?.[0] ||
        "Failed to upload document. Please try again.";

      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const resetModal = () => {
    setSelectedFile(null);
    setDocumentName("");
    setUploadProgress(0);
    setIsUploading(false);
    setShowUploadModal(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString();
  };

  const handleConfirmAction = async () => {
    if (confirmModal.type === "delete") {
      await handleDelete(confirmModal.documentId);
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <h1 className="text-3xl font-bold text-slate-900">
              Knowledge Base
            </h1>
            {isPolling && (
              <div className="flex items-center space-x-2 px-3 py-1 bg-blue-50 rounded-full">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-blue-600 font-medium">
                  Auto-refreshing
                </span>
              </div>
            )}
          </div>
          <p className="text-slate-600">
            Upload and manage your documents for the chatbot to learn from
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {/* Manual refresh and polling toggle */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => loadDocuments(currentPage)}
              disabled={loading}
              className="p-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="Refresh documents"
            >
              <svg
                className={`w-5 h-5 ${loading ? "animate-spin" : ""}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>

            {/* Manual polling toggle - only show if there are processing docs */}
            {documents.some((doc) => doc.status === "processing") && (
              <button
                onClick={isPolling ? stopPolling : startPolling}
                className={`p-2 rounded-lg transition-colors ${
                  isPolling
                    ? "text-blue-600 bg-blue-50 hover:bg-blue-100"
                    : "text-slate-600 hover:text-blue-600 hover:bg-blue-50"
                }`}
                title={isPolling ? "Stop auto-refresh" : "Start auto-refresh"}
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  {isPolling ? (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  ) : (
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m-5-7a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  )}
                </svg>
              </button>
            )}
          </div>
          <Button
            onClick={() => setShowUploadModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium"
          >
            <Upload className="w-5 h-5 mr-2" />
            Upload Document
          </Button>
        </div>
      </div>

      {documents.length > 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-8">
          <div
            className="overflow-x-auto overflow-y-auto"
            style={{ height: "400px" }}
          >
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200 sticky top-0 z-10">
                <tr>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">
                    Document
                  </th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">
                    Type
                  </th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">
                    Size
                  </th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">
                    Upload Date
                  </th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">
                    Status
                  </th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center">
                      <div className="flex items-center justify-center space-x-2 text-slate-500">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Loading documents...</span>
                      </div>
                    </td>
                  </tr>
                ) : documents.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      <div className="flex flex-col items-center space-y-2">
                        <FileText className="w-8 h-8 text-slate-300" />
                        <p>No documents found</p>
                        <p className="text-sm">
                          Upload your first document to get started
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  documents.map((document) => (
                    <tr
                      key={document.id}
                      className="hover:bg-slate-50 transition-colors"
                    >
                      <td className="py-4 px-6">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                            <FileText className="w-5 h-5 text-blue-600" />
                          </div>
                          {editingDocId === document.id ? (
                            <div className="flex items-center space-x-2">
                              <Input
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                                className="text-sm"
                                onKeyDown={(e) => {
                                  if (e.key === "Enter")
                                    handleEditSave(document.id);
                                  if (e.key === "Escape") handleEditCancel();
                                }}
                                autoFocus
                              />
                              <button
                                onClick={() => handleEditSave(document.id)}
                                className="p-1 text-green-600 hover:text-green-700"
                                disabled={isSubmitting}
                              >
                                <Check className="w-4 h-4" />
                              </button>
                              <button
                                onClick={handleEditCancel}
                                className="p-1 text-slate-500 hover:text-slate-700"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          ) : (
                            <span className="font-medium text-slate-900">
                              {document.name}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                          {document.file_type?.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-slate-600">
                        {formatFileSize(document.size_bytes)}
                      </td>
                      <td className="py-4 px-6 text-slate-600">
                        {formatDate(document.upload_date)}
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(document.status)}
                          <span className="text-sm font-medium text-slate-700">
                            {getStatusText(document.status)}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleDownload(document)}
                            disabled={document.status !== "ready"}
                            className={`p-2 rounded-lg transition-colors ${
                              document.status === "ready"
                                ? "text-slate-600 hover:text-blue-600 hover:bg-blue-50"
                                : "text-slate-300 cursor-not-allowed"
                            }`}
                            title={
                              document.status === "ready"
                                ? "Download document"
                                : `Document is ${document.status} - download not available`
                            }
                          >
                            <Download className="w-4 h-4" />
                          </button>
                          
                          {/* Reprocess button - only show for failed documents */}
                          {document.status === "failed" && (
                            <button
                              onClick={() => handleReprocess(document)}
                              disabled={isSubmitting}
                              className="p-2 text-slate-600 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
                              title="Reprocess document"
                            >
                              <RotateCcw className="w-4 h-4" />
                            </button>
                          )}
                          
                          {editingDocId !== document.id && (
                            <button
                              onClick={() => handleEditStart(document)}
                              className="p-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                              disabled={isSubmitting}
                              title="Edit document name"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() =>
                              setConfirmModal({
                                show: true,
                                type: "delete",
                                documentId: document.id,
                                documentName: document.name,
                              })
                            }
                            className="p-2 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            disabled={isSubmitting}
                            title="Delete document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <TablePagination
            paginationData={paginationData}
            currentPage={currentPage}
            onPageChange={handlePageChange}
            isLoading={loading}
          />
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-slate-500" />
          </div>
          <h3 className="text-xl font-semibold text-slate-900 mb-2">
            No documents uploaded yet
          </h3>
          <p className="text-slate-600 mb-6">
            Start by uploading your first document to train your chatbot
          </p>
          <Button
            onClick={() => setShowUploadModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium"
          >
            <Upload className="w-5 h-5 mr-2" />
            Upload Your First Document
          </Button>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-slate-900">
                Upload a New Document
              </h3>
              <button
                onClick={resetModal}
                className="text-slate-500 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-6">
              {!selectedFile ? (
                <div
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                    dragActive
                      ? "border-blue-500 bg-blue-50"
                      : "border-slate-300 hover:border-slate-400"
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Upload className="w-6 h-6 text-slate-500" />
                  </div>
                  <p className="text-slate-600 mb-4">
                    Drag and drop your document here, or
                  </p>
                  <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    accept=".pdf,.docx,.txt,.md,.csv"
                    onChange={(e) =>
                      e.target.files?.[0] && handleFileSelect(e.target.files[0])
                    }
                  />
                  <Button
                    onClick={() =>
                      document.getElementById("file-upload")?.click()
                    }
                    variant="outline"
                    className="rounded-xl"
                  >
                    Choose File
                  </Button>
                  <p className="text-xs text-slate-500 mt-4">
                    Supports PDF, DOCX, TXT, MD, CSV • Max 10MB
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="p-4 bg-slate-50 rounded-xl">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
                        <FileText className="w-5 h-5 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-slate-900">
                          {selectedFile.name}
                        </p>
                        <p className="text-sm text-slate-600">
                          {formatFileSize(selectedFile.size)} •{" "}
                          {selectedFile.type || "Unknown type"}
                        </p>
                      </div>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="text-slate-500 hover:text-slate-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div>
                    <Label
                      htmlFor="document-name"
                      className="text-sm font-medium text-slate-700"
                    >
                      Document Name *
                    </Label>
                    <Input
                      id="document-name"
                      value={documentName}
                      onChange={(e) => setDocumentName(e.target.value)}
                      placeholder="Enter document name"
                      className="mt-2"
                      required
                    />
                  </div>

                  {isUploading && (
                    <div>
                      <div className="flex justify-between text-sm text-slate-600 mb-2">
                        <span>Uploading...</span>
                        <span>{uploadProgress}%</span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div className="flex space-x-3">
                <Button
                  onClick={resetModal}
                  variant="outline"
                  className="flex-1 rounded-xl"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleUpload}
                  disabled={
                    !selectedFile || isUploading || !documentName.trim()
                  }
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-xl"
                >
                  {isUploading ? "Uploading..." : "Upload"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-slate-900">
                  Delete Document
                </h3>
                <p className="text-sm text-slate-600">
                  {confirmModal.documentName}
                </p>
              </div>
            </div>

            <p className="text-slate-600 mb-6">
              This action cannot be undone. The document will be permanently
              deleted from your knowledge base.
            </p>

            <div className="flex space-x-3">
              <Button
                onClick={() =>
                  setConfirmModal({
                    show: false,
                    type: "delete",
                    documentId: "",
                    documentName: "",
                  })
                }
                variant="outline"
                className="flex-1 rounded-xl"
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmAction}
                disabled={isSubmitting}
                className="flex-1 rounded-xl bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  "Delete"
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
