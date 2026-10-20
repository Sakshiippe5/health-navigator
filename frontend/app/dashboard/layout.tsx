'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Heart, FileText, MessageSquare, Activity,
  Pill, Calendar, LogOut, User, Menu, X,
  LayoutDashboard, ChevronRight
} from 'lucide-react'
import { getUser, logout } from '@/lib/auth'

const navItems = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard, exact: true },
  { href: '/dashboard/documents', label: 'Documents', icon: FileText },
  { href: '/dashboard/chat', label: 'Chat with PDF', icon: MessageSquare },
  { href: '/dashboard/symptoms', label: 'Symptom Checker', icon: Activity },
  { href: '/dashboard/drugs', label: 'Drug Interactions', icon: Pill },
  { href: '/dashboard/schedule', label: 'Appointment', icon: Calendar },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const u = getUser()
    if (!u) {
      router.push('/login')
      return
    }
    setUser(u)
  }, [])

  const isActive = (item: any) => {
    if (item.exact) return pathname === item.href
    return pathname.startsWith(item.href)
  }

  return (
    <div className="min-h-screen bg-[#F0F9FF] flex">

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-sky-100 
        flex flex-col transform transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:relative lg:translate-x-0
      `}>

        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-sky-50">
          <div className="w-9 h-9 bg-sky-500 rounded-xl flex items-center justify-center shadow-sm">
            <Heart className="text-white" size={18} />
          </div>
          <div>
            <p className="font-bold text-slate-800 leading-none">Health</p>
            <p className="font-bold text-sky-500 leading-none">Navigator</p>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="ml-auto lg:hidden text-slate-400">
            <X size={20} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mb-3">
            Menu
          </p>
          {navItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item)
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-xl transition group
                  ${active
                    ? 'bg-sky-50 text-sky-700 font-medium'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                  }
                `}
              >
                <Icon size={18} className={active ? 'text-sky-600' : 'text-slate-400 group-hover:text-slate-600'} />
                <span className="text-sm">{item.label}</span>
                {active && <ChevronRight size={14} className="ml-auto text-sky-400" />}
              </Link>
            )
          })}
        </nav>

        {/* User */}
        <div className="p-3 border-t border-sky-50">
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-50 mb-1">
            <div className="w-8 h-8 bg-sky-100 rounded-full flex items-center justify-center flex-shrink-0">
              <User size={15} className="text-sky-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-800 truncate">
                {user?.full_name || 'User'}
              </p>
              <p className="text-xs text-slate-400 truncate">
                {user?.email}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2.5 w-full text-red-500 hover:bg-red-50 rounded-xl transition text-sm"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Mobile header */}
        <header className="lg:hidden bg-white border-b border-sky-100 px-4 py-3 flex items-center gap-3">
          <button onClick={() => setSidebarOpen(true)} className="text-slate-600">
            <Menu size={22} />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-sky-500 rounded-lg flex items-center justify-center">
              <Heart className="text-white" size={14} />
            </div>
            <span className="font-bold text-slate-800">Health Navigator</span>
          </div>
        </header>

        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>

      {/* Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)} />
      )}
    </div>
  )
}