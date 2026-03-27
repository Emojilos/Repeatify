import { useToastStore } from '../stores/toastStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface RequestOptions extends RequestInit {
  skipAuth?: boolean
  silent?: boolean
}

let isRefreshing = false
let refreshPromise: Promise<boolean> | null = null

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return false

  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) return false

    const data = await response.json()
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    return true
  } catch {
    return false
  }
}

function clearAuth() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  window.location.href = import.meta.env.BASE_URL + '#/auth/login'
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { skipAuth, silent, ...fetchOptions } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string>),
  }

  if (!skipAuth) {
    const token = localStorage.getItem('access_token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...fetchOptions,
      headers,
    })
  } catch (err) {
    const message = 'Не удалось подключиться к серверу. Проверьте соединение.'
    if (!silent) useToastStore.getState().addToast(message, 'error')
    throw new ApiError(0, message)
  }

  // On 401, try to refresh the token and retry the request once
  if (response.status === 401 && !skipAuth) {
    if (!isRefreshing) {
      isRefreshing = true
      refreshPromise = tryRefreshToken().finally(() => {
        isRefreshing = false
        refreshPromise = null
      })
    }

    const refreshed = await (refreshPromise ?? tryRefreshToken())

    if (refreshed) {
      // Retry with the new token
      const newToken = localStorage.getItem('access_token')
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`
      }
      const retryResponse = await fetch(`${API_URL}${path}`, {
        ...fetchOptions,
        headers,
      })
      if (retryResponse.ok) {
        return retryResponse.json() as Promise<T>
      }
    }

    // Refresh failed — force logout
    clearAuth()
    throw new ApiError(401, 'Сессия истекла. Войдите снова.')
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const message = body.detail || `Ошибка запроса: ${response.status}`
    if (!silent) useToastStore.getState().addToast(message, 'error')
    throw new ApiError(response.status, message)
  }

  return response.json() as Promise<T>
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}
