// app/dashboard/chat/page.tsx
'use client'

import { useState, useEffect, useRef } from 'react'
import {
  Send,
  FileText,
  Loader2,
  Bot,
  User,
  ChevronDown,
  Trash2
} from 'lucide-react'
import { documentAPI, chatAPI } from '@/lib/api'
import toast, { Toaster } from 'react-hot-toast'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
}

interface EmbeddedDoc {
  file_id: string
  collection_name: string
  total_chunks: number
}

export default function ChatPage() {
  const [embeddedDocs, setEmbeddedDocs] = useState<EmbeddedDoc[]>([])
  const [selectedFileId, setSelectedFileId] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadEmbeddedDocs()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadEmbeddedDocs = async () => {
    try {
      const data = await documentAPI.getEmbedded()
      setEmbeddedDocs(data.documents)
      if (data.documents.length > 0) {
        setSelectedFileId(data.documents[0].file_id)
      }
    } catch (error) {
      console.error('Failed to load documents')
    }
  }

  const handleSend = async () => {
    if (!input.trim() || !selectedFileId || loading) return

    const userMessage = input.trim()
    setInput('')

    // Add user message immediately
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage
    }])

    setLoading(true)
    try {
      const data = await chatAPI.sendMessage(
        selectedFileId,
        userMessage,
        sessionId || undefined
      )

      // Save session ID for conversation memory
      if (!sessionId) setSessionId(data.session_id)

      // Add AI response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources
      }])

    } catch (error: any) {
      toast.error('Failed to get response')
      // Remove the user message if request failed
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const handleClearChat = async () => {
    if (sessionId) {
      await chatAPI.clearHistory(sessionId)
    }
    setMessages([])
    setSessionId(null)
    toast.success('Chat cleared')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <Toaster position="top-center" />

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Chat with PDF</h1>
          <p className="text-gray-500 text-sm mt-1">
            Ask questions about your medical documents
          </p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClearChat}
            className="flex items-center gap-2 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition text-sm"
          >
            <Trash2 size={16} />
            Clear chat
          </button>
        )}
      </div>

      {/* Document Selector */}
      <div className="mb-4">
        {embeddedDocs.length === 0 ? (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-700">
            No embedded documents found. Go to{' '}
            <a href="/dashboard/documents" className="underline font-medium">
              Documents
            </a>{' '}
            and embed a PDF first.
          </div>
        ) : (
          <div className="relative">
            <FileText
              className="absolute left-3 top-3 text-gray-400"
              size={18}
            />
            <select
              value={selectedFileId}
              onChange={(e) => {
                setSelectedFileId(e.target.value)
                setMessages([])
                setSessionId(null)
              }}
              className="w-full pl-10 pr-10 py-2.5 bg-white border border-gray-300 rounded-xl appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {embeddedDocs.map((doc) => (
                <option key={doc.file_id} value={doc.file_id}>
                  {doc.collection_name.replace('doc_', '')} — {doc.total_chunks} chunks
                </option>
              ))}
            </select>
            <ChevronDown
              className="absolute right-3 top-3 text-gray-400 pointer-events-none"
              size={18}
            />
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto bg-white rounded-2xl border border-gray-100 p-4 space-y-4 mb-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Bot className="text-gray-300 mb-3" size={48} />
            <p className="text-gray-500 font-medium">
              Start a conversation
            </p>
            <p className="text-gray-400 text-sm mt-1">
              Ask anything about your selected document
            </p>
            <div className="mt-4 space-y-2">
              {[
                "What is the main diagnosis?",
                "What medications were prescribed?",
                "What are the test results?",
              ].map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => setInput(suggestion)}
                  className="block w-full text-left px-4 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm text-gray-600 transition"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot size={16} className="text-blue-600" />
                  </div>
                )}

                <div className={`max-w-[75%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                  <div className={`rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-sm'
                      : 'bg-gray-100 text-gray-900 rounded-tl-sm'
                  }`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </p>
                  </div>

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {msg.sources.slice(0, 2).map((source, si) => (
                        <div
                          key={si}
                          className="text-xs text-gray-400 bg-gray-50 rounded-lg px-3 py-2"
                        >
                          <span className="font-medium text-gray-500">
                            Source {si + 1}
                          </span>
                          {' · '}
                          {source.similarity_score.toFixed(2)} relevance
                          {' · '}
                          {source.excerpt.slice(0, 80)}...
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <User size={16} className="text-white" />
                  </div>
                )}
              </div>
            ))}

            {/* Loading indicator */}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot size={16} className="text-blue-600" />
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                  <Loader2 size={16} className="animate-spin text-gray-400" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              embeddedDocs.length === 0
                ? 'Embed a document first...'
                : 'Ask a question about your document...'
            }
            disabled={embeddedDocs.length === 0 || loading}
            rows={1}
            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:bg-gray-50 disabled:text-gray-400"
          />
        </div>
        <button
          onClick={handleSend}
          disabled={!input.trim() || !selectedFileId || loading}
          className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <Send size={18} />
          )}
        </button>
      </div>

      {/* Session info */}
      {sessionId && (
        <p className="text-xs text-gray-400 text-center mt-2">
          Session: {sessionId} · {messages.filter(m => m.role === 'user').length} messages
        </p>
      )}
    </div>
  )
}