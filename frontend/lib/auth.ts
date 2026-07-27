// lib/auth.ts
export interface User {
  id: number
  email: string
  full_name: string
  is_active: boolean
}

// Save token to both localStorage AND cookie
export const saveAuth = (token: string, user: User) => {
  localStorage.setItem('token', token)
  localStorage.setItem('user', JSON.stringify(user))
  // Cookie for middleware to read (server-side)
  document.cookie = `token=${token}; path=/; max-age=${60 * 60 * 24 * 7}` // 7 days
}

export const getToken = (): string | null => {
  return localStorage.getItem('token')
}

export const getUser = (): User | null => {
  const user = localStorage.getItem('user')
  return user ? JSON.parse(user) : null
}

export const isLoggedIn = (): boolean => {
  return !!getToken()
}

export const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  // Clear cookie
  document.cookie = 'token=; path=/; max-age=0'
  window.location.href = '/login'
}