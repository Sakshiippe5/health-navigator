// app/dashboard/documents/page.tsx
'use client'

import { useState, useEffect, useRef } from 'react'
import {
  Upload,
  FileText,
  CheckCircle,
  Clock,
  Loader2,
  Brain,
  AlertCircle
} from 'lucide-react'
import { documentAPI } from '@/lib/api'
import toast, { Toaster } from 'react-hot-toast'

interface Document {
  filename: string
  size_mb: number
}

interface EmbeddedDoc {
  file_id: string
  collection_name: string
  total_chunks: number
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [embeddedDocs, setEmbeddedDocs] = useState<EmbeddedDoc[]>([])
  const [uploading, setUploading] = useState(false)
  const [embedding, setEmbedding] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadDocuments()
    loadEmbedded()
  }, [])

  const loadDocuments = async () => {
    try {
      const data = await documentAPI.list()
      setDocuments(data.documents)
    } catch (error) {
      console.error('Failed to load documents')
    }
  }

  const loadEmbedded = async () => {
    try {
      const data = await documentAPI.getEmbedded()
      setEmbeddedDocs(data.documents)
    } catch (error) {
      console.error('Failed to load embedded docs')
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.pdf')) {
      toast.error('Only PDF files are allowed')
      return
    }

    setUploading(true)
    try {
      const data = await documentAPI.upload(file)
      toast.success(`Uploaded: ${data.original_name}`)
      await loadDocuments()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleEmbed = async (fileId: string) => {
    setEmbedding(fileId)
    try {
      await documentAPI.embed(fileId)
      toast.success('Document embedded successfully!')
      await loadEmbedded()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Embedding failed')
    } finally {
      setEmbedding(null)
    }
  }

  const getFileId = (filename: string) => filename.split('_')[0]

  const isEmbedded = (filename: string) => {
    const fileId = getFileId(filename)
    return embeddedDocs.some(doc => doc.file_id === fileId)
  }

  const getChunkCount = (filename: string) => {
    const fileId = getFileId(filename)
    return embeddedDocs.find(doc => doc.file_id === fileId)?.total_chunks || 0
  }

  return (
    <div>
      <Toaster position="top-center" />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-500 mt-1">
            Upload medical PDFs and prepare them for AI analysis
          </p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition disabled:opacity-50"
        >
          {uploading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <Upload size={18} />
          )}
          {uploading ? 'Uploading...' : 'Upload PDF'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleUpload}
          className="hidden"
        />
      </div>

      {/* Documents List */}
      {documents.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border-2 border-dashed border-gray-200">
          <FileText className="mx-auto text-gray-300 mb-4" size={48} />
          <h3 className="text-gray-500 font-medium">No documents yet</h3>
          <p className="text-gray-400 text-sm mt-1">
            Upload a PDF to get started
          </p>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
          >
            Upload your first PDF
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {documents.map((doc, i) => {
            const fileId = getFileId(doc.filename)
            const embedded = isEmbedded(doc.filename)
            const chunks = getChunkCount(doc.filename)
            const isEmbedding = embedding === fileId

            return (
              <div
                key={i}
                className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex items-center gap-4"
              >
                {/* Icon */}
                <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText className="text-red-500" size={20} />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {doc.filename.split('_').slice(1).join('_')}
                  </p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-gray-400">
                      {doc.size_mb.toFixed(2)} MB
                    </span>
                    <span className="text-xs text-gray-300">•</span>
                    <span className="text-xs text-gray-400">
                      ID: {fileId}
                    </span>
                    {embedded && (
                      <>
                        <span className="text-xs text-gray-300">•</span>
                        <span className="text-xs text-green-600">
                          {chunks} chunks
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Status + Action */}
                <div className="flex items-center gap-3 flex-shrink-0">
                  {embedded ? (
                    <div className="flex items-center gap-1.5 text-green-600 bg-green-50 px-3 py-1.5 rounded-lg text-sm">
                      <CheckCircle size={14} />
                      Ready for chat
                    </div>
                  ) : (
                    <button
                      onClick={() => handleEmbed(fileId)}
                      disabled={isEmbedding}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 text-purple-700 hover:bg-purple-100 rounded-lg text-sm transition disabled:opacity-50"
                    >
                      {isEmbedding ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Brain size={14} />
                      )}
                      {isEmbedding ? 'Embedding...' : 'Embed for AI'}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Info Box */}
      <div className="mt-6 bg-blue-50 rounded-xl p-4 flex gap-3">
        <AlertCircle className="text-blue-500 flex-shrink-0 mt-0.5" size={18} />
        <div>
          <p className="text-sm font-medium text-blue-800">
            How it works
          </p>
          <p className="text-sm text-blue-600 mt-1">
            Upload a PDF → Click "Embed for AI" → Go to Chat to ask questions.
            Embedding converts your document into searchable AI vectors.
          </p>
        </div>
      </div>
    </div>
  )
}