// app/dashboard/schedule/page.tsx
'use client'

import { useState } from 'react'
import { Calendar, Loader2, Plus, X, Activity, Pill, Clock } from 'lucide-react'
import { agentAPI } from '@/lib/api'
import toast, { Toaster } from 'react-hot-toast'

const URGENCY_COLORS: Record<string, string> = {
  EMERGENCY: 'bg-red-100 text-red-700 border-red-200',
  HIGH:      'bg-orange-100 text-orange-700 border-orange-200',
  MEDIUM:    'bg-yellow-100 text-yellow-700 border-yellow-200',
  LOW:       'bg-green-100 text-green-700 border-green-200',
}

export default function SchedulePage() {
  const [symptoms, setSymptoms] = useState('')
  const [medications, setMedications] = useState<string[]>([''])
  const [age, setAge] = useState('')
  const [history, setHistory] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'symptoms' | 'drugs' | 'appointment'>('symptoms')

  const addMedication = () => {
    if (medications.length < 6) setMedications([...medications, ''])
  }

  const removeMedication = (i: number) => {
    setMedications(medications.filter((_, idx) => idx !== i))
  }

  const updateMedication = (i: number, val: string) => {
    const updated = [...medications]
    updated[i] = val
    setMedications(updated)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symptoms.trim()) return

    setLoading(true)
    setResult(null)

    const validMeds = medications.filter(m => m.trim())

    try {
      const data = await agentAPI.healthAssessment(
        symptoms,
        validMeds.length >= 2 ? validMeds : undefined,
        age ? parseInt(age) : undefined,
        history || undefined
      )
      setResult(data)
      setActiveTab('symptoms')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Pipeline failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Toaster position="top-center" />

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Complete Health Assessment
        </h1>
        <p className="text-gray-500 mt-1">
          Runs all 3 AI agents — symptom checker, drug detector, appointment planner
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">

        {/* Symptoms */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Symptoms <span className="text-red-500">*</span>
          </label>
          <textarea
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder="Describe all your symptoms in detail..."
            rows={3}
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        {/* Medications */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Current medications
            <span className="text-gray-400 font-normal ml-1">
              (optional, need 2+ for interaction check)
            </span>
          </label>
          <div className="space-y-2">
            {medications.map((med, i) => (
              <div key={i} className="flex gap-2">
                <div className="relative flex-1">
                  <Pill className="absolute left-3 top-3 text-gray-400" size={16} />
                  <input
                    type="text"
                    value={med}
                    onChange={(e) => updateMedication(i, e.target.value)}
                    placeholder={`Medication ${i + 1}`}
                    className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                {medications.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeMedication(i)}
                    className="p-2.5 text-red-400 hover:bg-red-50 rounded-xl"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={addMedication}
            className="flex items-center gap-1 text-sm text-blue-600 mt-2"
          >
            <Plus size={14} />
            Add medication
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
            <input
              type="number"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              placeholder="e.g. 55"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Medical history</label>
            <input
              type="text"
              value={history}
              onChange={(e) => setHistory(e.target.value)}
              placeholder="e.g. diabetes, heart disease"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !symptoms.trim()}
          className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Running all 3 agents...
            </>
          ) : (
            <>
              <Calendar size={18} />
              Run Complete Assessment
            </>
          )}
        </button>
      </form>

      {/* Results */}
      {result && (
        <div className="space-y-4">

          {/* Overall Urgency */}
          <div className={`rounded-2xl border-2 p-5 ${URGENCY_COLORS[result.overall_urgency] || 'bg-gray-100'}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-bold text-xl">
                  Overall Urgency: {result.overall_urgency}
                </p>
                <p className="text-sm opacity-80 mt-1">
                  {result.summary?.immediate_action}
                </p>
              </div>
              <div className="text-right text-sm opacity-70">
                {result.pipeline_metadata?.duration_seconds}s
                · {result.pipeline_metadata?.agents_run?.length} agents
              </div>
            </div>
          </div>

          {/* Key Findings */}
          {result.summary?.key_findings?.length > 0 && (
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3">Key Findings</h3>
              <ul className="space-y-2">
                {result.summary.key_findings.map((finding: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-1.5 flex-shrink-0" />
                    {finding}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Tabs */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="flex border-b border-gray-100">
              {[
                { id: 'symptoms', label: 'Symptom Assessment', icon: Activity },
                { id: 'drugs', label: 'Drug Safety', icon: Pill },
                { id: 'appointment', label: 'Appointment Plan', icon: Calendar },
              ].map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition ${
                      activeTab === tab.id
                        ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    <Icon size={16} />
                    {tab.label}
                  </button>
                )
              })}
            </div>

            <div className="p-5">
              {/* Symptom Tab */}
              {activeTab === 'symptoms' && result.symptom_assessment && (
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold text-gray-900">
                      {result.symptom_assessment.severity_score}/10
                    </span>
                    <span className="text-gray-500">severity score</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      Possible conditions:
                    </p>
                    <ul className="space-y-1">
                      {result.symptom_assessment.possible_conditions?.map(
                        (c: string, i: number) => (
                          <li key={i} className="text-sm text-gray-600 flex items-center gap-2">
                            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                            {c}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Specialist: </span>
                    {result.symptom_assessment.specialist_needed}
                  </p>
                </div>
              )}

              {/* Drug Tab */}
              {activeTab === 'drugs' && (
                <div>
                  {result.drug_interactions ? (
                    <div className="space-y-3">
                      <p className="font-medium text-gray-900">
                        Overall risk: {result.drug_interactions.overall_risk}
                      </p>
                      <p className="text-sm text-gray-600">
                        {result.drug_interactions.summary}
                      </p>
                      {result.drug_interactions.interactions?.dangerous?.map(
                        (d: any, i: number) => (
                          <div key={i} className="bg-red-50 rounded-lg p-3 text-sm">
                            <p className="font-medium text-red-700">
                              ⚠️ {d.drug1} + {d.drug2}
                            </p>
                            <p className="text-red-600 mt-1">{d.clinical_effect}</p>
                          </div>
                        )
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-400 text-sm">
                      No medications provided or less than 2 medications entered.
                    </p>
                  )}
                </div>
              )}

              {/* Appointment Tab */}
              {activeTab === 'appointment' && result.appointment_plan && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Clock size={16} className="text-blue-500" />
                    <span className="font-medium text-gray-900">
                      {result.appointment_plan.timeframe}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Type: </span>
                    {result.appointment_plan.appointment_type}
                  </p>
                  {result.appointment_plan.preparation?.what_to_bring?.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-2">
                        What to bring:
                      </p>
                      <ul className="space-y-1">
                        {result.appointment_plan.preparation.what_to_bring.map(
                          (item: string, i: number) => (
                            <li key={i} className="text-sm text-gray-600 flex items-center gap-2">
                              <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                              {item}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}
                  {result.appointment_plan.preparation?.red_flags?.length > 0 && (
                    <div className="bg-red-50 rounded-lg p-3">
                      <p className="text-sm font-medium text-red-700 mb-1">
                        🚨 Go to ER immediately if:
                      </p>
                      {result.appointment_plan.preparation.red_flags.map(
                        (flag: string, i: number) => (
                          <p key={i} className="text-sm text-red-600">• {flag}</p>
                        )
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Next Steps */}
          {result.summary?.next_steps?.length > 0 && (
            <div className="bg-blue-50 rounded-xl p-5">
              <h3 className="font-semibold text-blue-900 mb-3">Next Steps</h3>
              <ul className="space-y-2">
                {result.summary.next_steps.map((step: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-blue-800">
                    <span className="font-bold flex-shrink-0">{i + 1}.</span>
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-xs text-gray-400 text-center">
            ⚠️ AI assessment only. Always consult qualified healthcare providers.
          </p>
        </div>
      )}
    </div>
  )
}