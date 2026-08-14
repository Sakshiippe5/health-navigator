// app/dashboard/symptoms/page.tsx
'use client'

import { useState } from 'react'
import {
  Activity,
  Loader2,
  AlertTriangle,
  CheckCircle,
  User,
  Stethoscope,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import { agentAPI } from '@/lib/api'
import toast, { Toaster } from 'react-hot-toast'

const URGENCY_CONFIG = {
  EMERGENCY: { color: 'bg-red-100 text-red-700 border-red-200', icon: '🚨', label: 'Emergency' },
  HIGH:      { color: 'bg-orange-100 text-orange-700 border-orange-200', icon: '⚠️', label: 'High' },
  MEDIUM:    { color: 'bg-yellow-100 text-yellow-700 border-yellow-200', icon: '⚡', label: 'Medium' },
  LOW:       { color: 'bg-green-100 text-green-700 border-green-200', icon: '✅', label: 'Low' },
}

export default function SymptomsPage() {
  const [symptoms, setSymptoms] = useState('')
  const [age, setAge] = useState('')
  const [history, setHistory] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [showSteps, setShowSteps] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symptoms.trim()) return

    setLoading(true)
    setResult(null)

    try {
      const data = await agentAPI.checkSymptoms(
        symptoms,
        age ? parseInt(age) : undefined,
        history || undefined
      )
      setResult(data)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Agent failed')
    } finally {
      setLoading(false)
    }
  }

  const urgencyConfig = result
    ? URGENCY_CONFIG[result.urgency_level as keyof typeof URGENCY_CONFIG]
    : null

  return (
    <div className="max-w-3xl mx-auto">
      <Toaster position="top-center" />

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Symptom Checker</h1>
        <p className="text-gray-500 mt-1">
          AI-powered triage assessment using LangGraph agents
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">

        {/* Symptoms */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Describe your symptoms <span className="text-red-500">*</span>
          </label>
          <textarea
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder="e.g. I have severe chest pain and shortness of breath that started 2 hours ago..."
            rows={4}
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Age */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Age (optional)
            </label>
            <div className="relative">
              <User className="absolute left-3 top-3 text-gray-400" size={16} />
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="e.g. 45"
                min="0"
                max="120"
                className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Medical History */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Medical history (optional)
            </label>
            <input
              type="text"
              value={history}
              onChange={(e) => setHistory(e.target.value)}
              placeholder="e.g. diabetes, hypertension"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !symptoms.trim()}
          className="w-full py-3 bg-orange-500 text-white rounded-xl font-semibold hover:bg-orange-600 transition disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Agent analyzing symptoms...
            </>
          ) : (
            <>
              <Activity size={18} />
              Check Symptoms
            </>
          )}
        </button>
      </form>

      {/* Results */}
      {result && (
        <div className="space-y-4">

          {/* Urgency Banner */}
          <div className={`rounded-2xl border-2 p-5 ${urgencyConfig?.color}`}>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">{urgencyConfig?.icon}</span>
              <div>
                <p className="font-bold text-lg">
                  {urgencyConfig?.label} Urgency
                </p>
                <p className="text-sm opacity-80">
                  Severity score: {result.severity_score}/10
                </p>
              </div>
            </div>
            <p className="font-medium mt-2">
              {result.recommended_action}
            </p>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* Possible Conditions */}
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Stethoscope size={18} className="text-blue-500" />
                Possible Conditions
              </h3>
              <ul className="space-y-2">
                {result.possible_conditions?.map((condition: string, i: number) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0" />
                    {condition}
                  </li>
                ))}
              </ul>
            </div>

            {/* Specialist + Categories */}
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3">
                Assessment Details
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">
                    Specialist Needed
                  </p>
                  <p className="text-sm font-medium text-gray-800">
                    {result.specialist_needed}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">
                    Body Systems
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.symptom_categories?.map((cat: string, i: number) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Follow-up Questions */}
          {result.follow_up_questions?.length > 0 && (
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3">
                Follow-up Questions Asked by Agent
              </h3>
              <ul className="space-y-2">
                {result.follow_up_questions.map((q: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="font-medium text-gray-400 flex-shrink-0">
                      {i + 1}.
                    </span>
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Agent Steps */}
          <div className="bg-gray-50 rounded-xl border border-gray-200">
            <button
              onClick={() => setShowSteps(!showSteps)}
              className="w-full px-5 py-3 flex items-center justify-between text-sm text-gray-600 hover:text-gray-900"
            >
              <span className="font-medium">
                Agent steps taken ({result.steps_taken?.length})
              </span>
              {showSteps ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
            {showSteps && (
              <div className="px-5 pb-4 space-y-1.5">
                {result.steps_taken?.map((step: string, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-gray-500">
                    <CheckCircle size={14} className="text-green-500 flex-shrink-0" />
                    {step}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Disclaimer */}
          <p className="text-xs text-gray-400 text-center">
            ⚠️ This is an AI assessment tool, not a medical diagnosis.
            Always consult a qualified healthcare provider.
          </p>
        </div>
      )}
    </div>
  )
}