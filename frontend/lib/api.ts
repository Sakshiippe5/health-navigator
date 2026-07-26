// lib/api.ts
//
// RESPONSIBILITY: All API calls to the FastAPI backend.
// Centralizing here means:
//   - One place to change the base URL
//   - Automatic token injection
//   - Consistent error handling

import axios from 'axios'

// Base URL of your FastAPI backend
const BASE_URL = 'http://localhost:8000/api/v1'

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request Interceptor ────────────────────────────────────────────────────
// Automatically adds JWT token to every request
// You don't have to manually add it in every API call
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response Interceptor ───────────────────────────────────────────────────
// If token expired → redirect to login automatically
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ── Auth API calls ─────────────────────────────────────────────────────────

export const authAPI = {
  register: async (email: string, fullName: string, password: string) => {
    const response = await api.post('/auth/register', {
      email,
      full_name: fullName,
      password,
    })
    return response.data
  },

  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', {
      email,
      password,
    })
    return response.data
  },

  getMe: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

// ── Document API calls ─────────────────────────────────────────────────────

export const documentAPI = {
  upload: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  list: async () => {
    const response = await api.get('/documents')
    return response.data
  },

  embed: async (fileId: string) => {
    const response = await api.post(`/documents/${fileId}/embed`)
    return response.data
  },

  getEmbedded: async () => {
    const response = await api.get('/documents/embedded')
    return response.data
  },
}

// ── Chat API calls ─────────────────────────────────────────────────────────

export const chatAPI = {
  sendMessage: async (
    fileId: string,
    question: string,
    sessionId?: string
  ) => {
    const response = await api.post(`/chat/${fileId}`, {
      question,
      session_id: sessionId,
      n_chunks: 3,
    })
    return response.data
  },

  getHistory: async (sessionId: string) => {
    const response = await api.get(`/chat/${sessionId}/history`)
    return response.data
  },

  clearHistory: async (sessionId: string) => {
    const response = await api.delete(`/chat/${sessionId}`)
    return response.data
  },
}

// ── Agent API calls ────────────────────────────────────────────────────────

export const agentAPI = {
  checkSymptoms: async (
    symptoms: string,
    patientAge?: number,
    medicalHistory?: string
  ) => {
    const response = await api.post('/agents/symptom-check', {
      symptoms,
      patient_age: patientAge,
      medical_history: medicalHistory,
    })
    return response.data
  },

  checkDrugInteractions: async (
    medications: string[],
    patientAge?: number,
    conditions?: string
  ) => {
    const response = await api.post('/agents/drug-interactions', {
      medications,
      patient_age: patientAge,
      conditions,
    })
    return response.data
  },

  healthAssessment: async (
    symptoms: string,
    medications?: string[],
    patientAge?: number,
    medicalHistory?: string
  ) => {
    const response = await api.post('/agents/health-assessment', {
      symptoms,
      medications,
      patient_age: patientAge,
      medical_history: medicalHistory,
    })
    return response.data
  },
}

export default api