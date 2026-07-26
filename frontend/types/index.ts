// types/index.ts
// All TypeScript interfaces matching our FastAPI schemas

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: number
  email: string
  full_name: string
}

export interface Document {
  filename: string
  size_mb: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  status: string
  session_id: string
  question: string
  answer: string
  history_length: number
  sources: Source[]
  model: string
}

export interface Source {
  chunk_index: number
  similarity_score: number
  excerpt: string
}

export interface SymptomCheckResult {
  symptoms_reported: string
  severity_score: number
  symptom_categories: string[]
  possible_conditions: string[]
  urgency_level: string
  recommended_action: string
  specialist_needed: string
  steps_taken: string[]
}