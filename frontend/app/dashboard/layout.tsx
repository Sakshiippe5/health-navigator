// app/dashboard/layout.tsx
// Shared layout for all dashboard pages
// Sidebar + main content area

'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Heart,
  FileText,
  MessageSquare,
  Activity,
  Pill,
  Calendar,
  LogOut,
  User,
  Menu,
  X
} from 'lucide-react'
import { getUser, logout } from '@/lib/auth'

const navItems = [
  { href: '/dashboard', label: 'Overview', icon: Activity },
  { href: '/dashboard/documents', label: 'Documents', icon: FileText },
  { href: '/dashboard/chat', label: 'Chat with PDF', icon: MessageSquare },
  { href: '/dashboard/symptoms', label: 'Symptom Checker', icon: Activity },
  { href: '/dashboard/drugs', label: 'Drug Interactions', icon: Pill },
  { href: '/dashboard/schedule', label: 'Appointment', icon: Calendar },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const [user, setUser] = useState<any>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    setUser(getUser())
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 flex">

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:relative lg:translate-x-0
      `}>

        {/* Logo */}
        <div className="flex items-center gap-2 p-6 border-b">
          <Heart className="text-red-500" size={24} />
          <span className="font-bold text-gray-900">Health Navigator</span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-auto lg:hidden"
          >
            <X size={20} />
          </button>
        </div>

        {/* Nav Items */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-xl transition
                  ${isActive
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                  }
                `}
              >
                <Icon size={20} />
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* User + Logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t">
          <div className="flex items-center gap-3 px-4 py-3 mb-2">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <User size={16} className="text-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.full_name || 'User'}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {user?.email || ''}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-3 px-4 py-3 w-full text-red-600 hover:bg-red-50 rounded-xl transition"
          >
            <LogOut size={20} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Mobile Header */}
        <header className="lg:hidden bg-white border-b px-4 py-3 flex items-center gap-3">
          <button onClick={() => setSidebarOpen(true)}>
            <Menu size={24} />
          </button>
          <Heart className="text-red-500" size={20} />
          <span className="font-bold text-gray-900">Health Navigator</span>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}