// lib/auth.ts
// Handles token storage and user session management

export interface User {
  id: number
  email: string
  full_name: string
  is_active: boolean
}

export const saveAuth = (token: string, user: User) => {
  localStorage.setItem('token', token)
  localStorage.setItem('user', JSON.stringify(user))
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
  window.location.href = '/login'
}