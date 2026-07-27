// app/dashboard/page.tsx
'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  FileText,
  MessageSquare,
  Activity,
  Pill,
  Calendar,
  ArrowRight
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
      setDocCount(data.total)
    } catch (error) {
      console.error('Failed to load documents')
    }
  }

  const features = [
    {
      href: '/dashboard/documents',
      icon: <FileText className="text-blue-500" size={28} />,
      title: 'Documents',
      description: 'Upload and manage medical PDFs',
      color: 'bg-blue-50 border-blue-100',
    },
    {
      href: '/dashboard/chat',
      icon: <MessageSquare className="text-green-500" size={28} />,
      title: 'Chat with PDF',
      description: 'Ask questions about your documents',
      color: 'bg-green-50 border-green-100',
    },
    {
      href: '/dashboard/symptoms',
      icon: <Activity className="text-orange-500" size={28} />,
      title: 'Symptom Checker',
      description: 'AI-powered symptom triage',
      color: 'bg-orange-50 border-orange-100',
    },
    {
      href: '/dashboard/drugs',
      icon: <Pill className="text-red-500" size={28} />,
      title: 'Drug Interactions',
      description: 'Check medication safety',
      color: 'bg-red-50 border-red-100',
    },
    {
      href: '/dashboard/schedule',
      icon: <Calendar className="text-purple-500" size={28} />,
      title: 'Appointment',
      description: 'Plan your medical visits',
      color: 'bg-purple-50 border-purple-100',
    },
  ]

  return (
    <div>
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.full_name?.split(' ')[0] || 'there'} 👋
        </h1>
        <p className="text-gray-500 mt-1">
          What would you like to do today?
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Documents uploaded', value: docCount },
          { label: 'AI agents available', value: 3 },
          { label: 'Features ready', value: 5 },
        ].map((stat, i) => (
          <div key={i} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <p className="text-3xl font-bold text-blue-600">{stat.value}</p>
            <p className="text-gray-500 text-sm mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Feature Cards */}
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Quick Actions
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {features.map((feature, i) => (
          <Link
            key={i}
            href={feature.href}
            className={`block p-6 rounded-xl border-2 ${feature.color} hover:shadow-md transition group`}
          >
            <div className="flex items-start justify-between">
              <div className="mb-3">{feature.icon}</div>
              <ArrowRight
                size={18}
                className="text-gray-400 group-hover:text-gray-600 transition"
              />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">
              {feature.title}
            </h3>
            <p className="text-sm text-gray-500">{feature.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}