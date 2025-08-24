
import React, { useState } from 'react';
import { Upload, FileText, Trash2, Eye, Clock, CheckCircle, AlertCircle, X, Edit2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';

interface Document {
  id: string;
  filename: string;
  filetype: string;
  uploadDate: string;
  status: 'processing' | 'ready' | 'error';
  size: string;
}

const mockDocuments: Document[] = [
  {
    id: '1',
    filename: 'Employee Handbook.pdf',
    filetype: 'PDF',
    uploadDate: '2024-01-15',
    status: 'ready',
    size: '2.4 MB'
  },
  {
    id: '2',
    filename: 'Product Documentation.docx',
    filetype: 'DOCX',
    uploadDate: '2024-01-14',
    status: 'processing',
    size: '1.8 MB'
  },
  {
    id: '3',
    filename: 'Company Policies.pdf',
    filetype: 'PDF',
    uploadDate: '2024-01-13',
    status: 'ready',
    size: '3.2 MB'
  }
];

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>(mockDocuments);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentName, setDocumentName] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [editingDocId, setEditingDocId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: Document['status']) => {
    switch (status) {
      case 'ready':
        return 'Ready';
      case 'processing':
        return 'Processing';
      case 'error':
        return 'Error';
      default:
        return '';
    }
  };

  const handleDelete = (id: string) => {
    setDocuments(documents.filter(doc => doc.id !== id));
    toast({
      title: "Document deleted",
      description: "The document has been removed from your knowledge base",
    });
  };

  const handleEditStart = (doc: Document) => {
    setEditingDocId(doc.id);
    setEditName(doc.filename);
  };

  const handleEditSave = (docId: string) => {
    if (!editName.trim()) {
      toast({
        title: "Error",
        description: "Document name cannot be empty",
        variant: "destructive",
      });
      return;
    }

    setDocuments(documents.map(doc => 
      doc.id === docId ? { ...doc, filename: editName.trim() } : doc
    ));
    setEditingDocId(null);
    setEditName('');
    
    toast({
      title: "Document renamed",
      description: "The document name has been updated successfully",
    });
  };

  const handleEditCancel = () => {
    setEditingDocId(null);
    setEditName('');
  };

  const handleFileSelect = (file: File) => {
    // Validate file type
    const allowedTypes = ['.pdf', '.docx', '.txt', '.md', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
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
    setDocumentName(file.name.split('.')[0]);
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

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + 10;
      });
    }, 200);

    // Simulate upload completion
    setTimeout(() => {
      const newDocument: Document = {
        id: (Date.now()).toString(),
        filename: documentName.trim() + '.' + selectedFile.name.split('.').pop(),
        filetype: selectedFile.name.split('.').pop()?.toUpperCase() || 'FILE',
        uploadDate: new Date().toISOString().split('T')[0],
        status: 'processing',
        size: (selectedFile.size / (1024 * 1024)).toFixed(1) + ' MB'
      };

      setDocuments(prev => [newDocument, ...prev]);
      setShowUploadModal(false);
      setSelectedFile(null);
      setDocumentName('');
      setUploadProgress(0);
      setIsUploading(false);

      toast({
        title: "Document uploaded successfully",
        description: "Your document is being processed and will be ready shortly",
      });

      // Simulate processing completion
      setTimeout(() => {
        setDocuments(prev => prev.map(doc => 
          doc.id === newDocument.id 
            ? { ...doc, status: 'ready' as const }
            : doc
        ));
      }, 3000);
    }, 2000);
  };

  const resetModal = () => {
    setSelectedFile(null);
    setDocumentName('');
    setUploadProgress(0);
    setIsUploading(false);
    setShowUploadModal(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Knowledge Base</h1>
          <p className="text-slate-600">Upload and manage your documents for the chatbot to learn from</p>
        </div>
        <Button 
          onClick={() => setShowUploadModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium"
        >
          <Upload className="w-5 h-5 mr-2" />
          Upload Document
        </Button>
      </div>

      {documents.length > 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">Document</th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">Type</th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">Size</th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">Upload Date</th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">Status</th>
                  <th className="text-left py-4 px-6 font-semibold text-slate-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {documents.map((document) => (
                  <tr key={document.id} className="hover:bg-slate-50 transition-colors">
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
                                if (e.key === 'Enter') handleEditSave(document.id);
                                if (e.key === 'Escape') handleEditCancel();
                              }}
                              autoFocus
                            />
                            <button
                              onClick={() => handleEditSave(document.id)}
                              className="p-1 text-green-600 hover:text-green-700"
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
                          <span className="font-medium text-slate-900">{document.filename}</span>
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                        {document.filetype}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-slate-600">{document.size}</td>
                    <td className="py-4 px-6 text-slate-600">{document.uploadDate}</td>
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
                        <button className="p-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>
                        {editingDocId !== document.id && (
                          <button 
                            onClick={() => handleEditStart(document)}
                            className="p-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                        )}
                        <button 
                          onClick={() => handleDelete(document.id)}
                          className="p-2 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-slate-500" />
          </div>
          <h3 className="text-xl font-semibold text-slate-900 mb-2">No documents uploaded yet</h3>
          <p className="text-slate-600 mb-6">Start by uploading your first document to train your chatbot</p>
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
              <h3 className="text-xl font-semibold text-slate-900">Upload a New Document</h3>
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
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-slate-300 hover:border-slate-400'
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
                    onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                  />
                  <Button
                    onClick={() => document.getElementById('file-upload')?.click()}
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
                        <p className="font-medium text-slate-900">{selectedFile.name}</p>
                        <p className="text-sm text-slate-600">
                          {formatFileSize(selectedFile.size)} • {selectedFile.type || 'Unknown type'}
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
                    <Label htmlFor="document-name" className="text-sm font-medium text-slate-700">
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
                  disabled={!selectedFile || isUploading || !documentName.trim()}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded-xl"
                >
                  {isUploading ? 'Uploading...' : 'Upload'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
