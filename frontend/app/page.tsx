// app/page.tsx — Landing page
'use client'

import Link from 'next/link'
import { 
  Heart, 
  Brain, 
  FileText, 
  Shield,
  ArrowRight,
  Activity
} from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      
      {/* Navbar */}
      <nav className="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Heart className="text-red-500" size={24} />
          <span className="font-bold text-xl text-gray-800">
            Health Navigator
          </span>
        </div>
        <div className="flex gap-3">
          <Link
            href="/login"
            className="px-4 py-2 text-gray-600 hover:text-gray-900 transition"
          >
            Login
          </Link>
          <Link
            href="/register"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
          <Activity size={16} />
          AI-Powered Health Assistant
        </div>
        
        <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
          Your Personal
          <span className="text-blue-600"> Health Navigator</span>
        </h1>
        
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          Upload medical documents, check symptoms, detect drug interactions, 
          and get AI-powered health insights — all in one place.
        </p>
        
        <div className="flex gap-4 justify-center">
          <Link
            href="/register"
            className="flex items-center gap-2 px-8 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition text-lg"
          >
            Start Free
            <ArrowRight size={20} />
          </Link>
          <Link
            href="/login"
            className="px-8 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:border-gray-400 transition text-lg"
          >
            Login
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Everything you need
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              icon: <FileText className="text-blue-500" size={28} />,
              title: "PDF Analysis",
              description: "Upload medical reports and ask questions in plain English"
            },
            {
              icon: <Activity className="text-green-500" size={28} />,
              title: "Symptom Checker",
              description: "AI triage agent assesses symptoms and urgency level"
            },
            {
              icon: <Shield className="text-red-500" size={28} />,
              title: "Drug Interactions",
              description: "Detect dangerous medication combinations automatically"
            },
            {
              icon: <Brain className="text-purple-500" size={28} />,
              title: "Smart Scheduling",
              description: "Get specialist recommendations and appointment planning"
            },
          ].map((feature, i) => (
            <div
              key={i}
              className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition"
            >
              <div className="mb-4">{feature.icon}</div>
              <h3 className="font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-500 text-sm">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="text-center py-8 text-gray-400 text-sm">
        ⚠️ Not a replacement for professional medical advice.
        Always consult a qualified healthcare provider.
      </footer>
    </div>
  )
}