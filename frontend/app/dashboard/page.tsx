'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  FileText, MessageSquare, Activity,
  Pill, Calendar, ArrowRight, TrendingUp,
  Shield, Zap
} from 'lucide-react'
import { getUser } from '@/lib/auth'
import { documentAPI } from '@/lib/api'

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null)
  const [docCount, setDocCount] = useState(0)

  useEffect(() => {
    setUser(getUser())
    loadDocCount()
  }, [])

  const loadDocCount = async () => {
    try {
      const data = await documentAPI.list()
      setDocCount(data.total || 0)
    } catch {
      setDocCount(0)
    }
  }

  const features = [
    {
      href: '/dashboard/documents',
      icon: FileText,
      iconBg: 'bg-sky-50',
      iconColor: 'text-sky-500',
      borderColor: 'hover:border-sky-200',
      title: 'Documents',
      description: 'Upload and manage medical PDFs',
      tag: 'RAG',
      tagColor: 'bg-sky-50 text-sky-600 border-sky-100'
    },
    {
      href: '/dashboard/chat',
      icon: MessageSquare,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-500',
      borderColor: 'hover:border-emerald-200',
      title: 'Chat with PDF',
      description: 'Ask questions about your documents',
      tag: 'AI',
      tagColor: 'bg-emerald-50 text-emerald-600 border-emerald-100'
    },
    {
      href: '/dashboard/symptoms',
      icon: Activity,
      iconBg: 'bg-orange-50',
      iconColor: 'text-orange-500',
      borderColor: 'hover:border-orange-200',
      title: 'Symptom Checker',
      description: 'AI-powered symptom triage',
      tag: 'Agent',
      tagColor: 'bg-orange-50 text-orange-600 border-orange-100'
    },
    {
      href: '/dashboard/drugs',
      icon: Pill,
      iconBg: 'bg-red-50',
      iconColor: 'text-red-500',
      borderColor: 'hover:border-red-200',
      title: 'Drug Interactions',
      description: 'Check medication safety',
      tag: 'Agent',
      tagColor: 'bg-red-50 text-red-600 border-red-100'
    },
    {
      href: '/dashboard/schedule',
      icon: Calendar,
      iconBg: 'bg-purple-50',
      iconColor: 'text-purple-500',
      borderColor: 'hover:border-purple-200',
      title: 'Health Assessment',
      description: 'Complete AI health pipeline',
      tag: 'Pipeline',
      tagColor: 'bg-purple-50 text-purple-600 border-purple-100'
    },
  ]

  const firstName = user?.full_name?.split(' ')[0] || 'there'

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
          <span>Dashboard</span>
        </div>
        <h1 className="text-3xl font-bold text-slate-900">
          Good day, {firstName} 👋
        </h1>
        <p className="text-slate-500 mt-1">
          Your AI health assistant is ready to help.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {[
          {
            icon: <FileText size={20} />,
            label: 'Documents',
            value: docCount,
            bg: 'bg-sky-50',
            color: 'text-sky-600',
            border: 'border-sky-100'
          },
          {
            icon: <Zap size={20} />,
            label: 'AI Agents',
            value: 3,
            bg: 'bg-emerald-50',
            color: 'text-emerald-600',
            border: 'border-emerald-100'
          },
          {
            icon: <Shield size={20} />,
            label: 'Features',
            value: 5,
            bg: 'bg-purple-50',
            color: 'text-purple-600',
            border: 'border-purple-100'
          },
        ].map((stat, i) => (
          <div key={i}
            className={`bg-white rounded-2xl p-5 border ${stat.border} shadow-sm flex items-center gap-4`}>
            <div className={`w-12 h-12 ${stat.bg} rounded-xl flex items-center justify-center ${stat.color} flex-shrink-0`}>
              {stat.icon}
            </div>
            <div>
              <p className="text-3xl font-bold text-slate-900">{stat.value}</p>
              <p className="text-slate-500 text-sm">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((feature, i) => {
            const Icon = feature.icon
            return (
              <Link key={i} href={feature.href}
                className={`bg-white rounded-2xl p-5 border border-slate-100 shadow-sm ${feature.borderColor} hover:shadow-md transition group`}>
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-11 h-11 ${feature.iconBg} rounded-xl flex items-center justify-center`}>
                    <Icon size={20} className={feature.iconColor} />
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${feature.tagColor}`}>
                    {feature.tag}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-900 mb-1">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-500 mb-3">
                  {feature.description}
                </p>
                <div className="flex items-center text-xs font-medium text-sky-600 group-hover:gap-2 transition-all gap-1">
                  Open
                  <ArrowRight size={13} />
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Info banner */}
      <div className="bg-sky-50 border border-sky-100 rounded-2xl p-5 flex items-start gap-4">
        <div className="w-10 h-10 bg-sky-100 rounded-xl flex items-center justify-center flex-shrink-0">
          <TrendingUp size={18} className="text-sky-600" />
        </div>
        <div>
          <p className="font-medium text-sky-900">Getting started</p>
          <p className="text-sm text-sky-700 mt-0.5">
            Upload a medical PDF → Embed it → Chat with it using AI.
            Or use the Symptom Checker and Drug Interaction tools directly.
          </p>
        </div>
      </div>
    </div>
  )
}