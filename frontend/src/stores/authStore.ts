import { create } from 'zustand'
import { api, ApiError } from '../lib/api'

interface User {
  id: string
  email: string | null
  display_name: string | null
  exam_date: string | null
  target_score: number | null
  current_xp: number
  current_level: number
  current_streak: number
  has_diagnostic: boolean
  has_study_plan: boolean
}

interface AuthResponse {
  access_token: string
  refresh_token: string
  user_id: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  loadUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const data = await api<AuthResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
        skipAuth: true,
        silent: true,
      })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ token: data.access_token, isAuthenticated: true, isLoading: false })
      await get().loadUser()
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Ошибка входа'
      set({ isLoading: false, error: message })
      throw err
    }
  },

  register: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const data = await api<AuthResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
        skipAuth: true,
        silent: true,
      })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ token: data.access_token, isAuthenticated: true, isLoading: false })
      await get().loadUser()
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Ошибка регистрации'
      set({ isLoading: false, error: message })
      throw err
    }
  },

  logout: async () => {
    try {
      await api('/auth/logout', { method: 'POST', silent: true })
    } catch {
      // Ignore errors — clear local state regardless
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, token: null, isAuthenticated: false })
  },

  loadUser: async () => {
    try {
      const user = await api<User>('/api/users/me', { silent: true })
      set({ user })
    } catch {
      // Token might be invalid
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, token: null, isAuthenticated: false })
    }
  },

  clearError: () => set({ error: null }),
}))
