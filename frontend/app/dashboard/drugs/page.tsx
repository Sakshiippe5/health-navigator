// app/dashboard/drugs/page.tsx
'use client'

import { useState } from 'react'
import { Pill, Plus, X, Loader2, AlertTriangle, CheckCircle, Shield } from 'lucide-react'
import { agentAPI } from '@/lib/api'
import toast, { Toaster } from 'react-hot-toast'

const RISK_CONFIG = {
  SAFE:     { color: 'bg-green-100 text-green-700', icon: '✅' },
  LOW:      { color: 'bg-blue-100 text-blue-700', icon: '💙' },
  MODERATE: { color: 'bg-yellow-100 text-yellow-700', icon: '⚠️' },
  HIGH:     { color: 'bg-orange-100 text-orange-700', icon: '🔶' },
  CRITICAL: { color: 'bg-red-100 text-red-700', icon: '🚨' },
}

const SEVERITY_COLORS: Record<string, string> = {
  NONE:            'bg-gray-100 text-gray-600',
  MILD:            'bg-blue-100 text-blue-700',
  MODERATE:        'bg-yellow-100 text-yellow-700',
  SEVERE:          'bg-red-100 text-red-700',
  CONTRAINDICATED: 'bg-red-200 text-red-800',
}

export default function DrugsPage() {
  const [medications, setMedications] = useState<string[]>(['', ''])
  const [age, setAge] = useState('')
  const [conditions, setConditions] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const addMedication = () => {
    if (medications.length < 8) {
      setMedications([...medications, ''])
    }
  }

  const removeMedication = (index: number) => {
    if (medications.length > 2) {
      setMedications(medications.filter((_, i) => i !== index))
    }
  }

  const updateMedication = (index: number, value: string) => {
    const updated = [...medications]
    updated[index] = value
    setMedications(updated)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const validMeds = medications.filter(m => m.trim())
    if (validMeds.length < 2) {
      toast.error('Please enter at least 2 medications')
      return
    }

    setLoading(true)
    setResult(null)

    try {
      const data = await agentAPI.checkDrugInteractions(
        validMeds,
        age ? parseInt(age) : undefined,
        conditions || undefined
      )
      setResult(data)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Agent failed')
    } finally {
      setLoading(false)
    }
  }

  const allInteractions = result ? [
    ...(result.interactions?.dangerous || []),
    ...(result.interactions?.moderate || []),
    ...(result.interactions?.mild || []),
  ] : []

  return (
    <div className="max-w-3xl mx-auto">
      <Toaster position="top-center" />

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Drug Interactions</h1>
        <p className="text-gray-500 mt-1">
          Check medication safety using AI pharmacology agent
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">

        <label className="block text-sm font-medium text-gray-700 mb-3">
          Medications <span className="text-red-500">*</span>
          <span className="text-gray-400 font-normal ml-1">(minimum 2)</span>
        </label>

        <div className="space-y-2 mb-4">
          {medications.map((med, i) => (
            <div key={i} className="flex gap-2">
              <div className="relative flex-1">
                <Pill className="absolute left-3 top-3 text-gray-400" size={16} />
                <input
                  type="text"
                  value={med}
                  onChange={(e) => updateMedication(i, e.target.value)}
                  placeholder={`Medication ${i + 1} (e.g. Warfarin)`}
                  className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              {medications.length > 2 && (
                <button
                  type="button"
                  onClick={() => removeMedication(i)}
                  className="p-2.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition"
                >
                  <X size={18} />
                </button>
              )}
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={addMedication}
          disabled={medications.length >= 8}
          className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 mb-4 disabled:opacity-40"
        >
          <Plus size={16} />
          Add another medication
        </button>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Age (optional)
            </label>
            <input
              type="number"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              placeholder="e.g. 65"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Conditions (optional)
            </label>
            <input
              type="text"
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              placeholder="e.g. diabetes, atrial fibrillation"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-red-500 text-white rounded-xl font-semibold hover:bg-red-600 transition disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Agent checking interactions...
            </>
          ) : (
            <>
              <Shield size={18} />
              Check Interactions
            </>
          )}
        </button>
      </form>

      {/* Results */}
      {result && (
        <div className="space-y-4">

          {/* Overall Risk */}
          <div className={`rounded-2xl p-5 ${RISK_CONFIG[result.overall_risk as keyof typeof RISK_CONFIG]?.color || 'bg-gray-100'}`}>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">
                {RISK_CONFIG[result.overall_risk as keyof typeof RISK_CONFIG]?.icon}
              </span>
              <div>
                <p className="font-bold text-lg">
                  {result.overall_risk} Risk
                </p>
                <p className="text-sm opacity-80">
                  {result.interactions?.total_found} interaction(s) found
                  across {result.pairs_checked?.length} pairs checked
                </p>
              </div>
            </div>
            <p className="text-sm mt-2">{result.summary}</p>
          </div>

          {/* Interactions List */}
          {allInteractions.length > 0 && (
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-4">
                Interactions Found
              </h3>
              <div className="space-y-3">
                {allInteractions.map((interaction: any, i: number) => (
                  <div
                    key={i}
                    className="border border-gray-100 rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-medium text-gray-900">
                        {interaction.drug1} + {interaction.drug2}
                      </p>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLORS[interaction.severity] || 'bg-gray-100 text-gray-600'}`}>
                        {interaction.severity}
                      </span>
                    </div>
                    {interaction.clinical_effect && (
                      <p className="text-sm text-gray-600 mb-1">
                        {interaction.clinical_effect}
                      </p>
                    )}
                    {interaction.recommendation && (
                      <p className="text-xs text-gray-400">
                        💡 {interaction.recommendation}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations?.length > 0 && (
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3">
                Recommendations
              </h3>
              <ul className="space-y-2">
                {result.recommendations.map((rec: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle size={16} className="text-green-500 flex-shrink-0 mt-0.5" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-xs text-gray-400 text-center">
            ⚠️ AI assessment only. Always consult your pharmacist or doctor.
          </p>
        </div>
      )}
    </div>
  )
}