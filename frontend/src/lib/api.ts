import { useToastStore } from '../stores/toastStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface RequestOptions extends RequestInit {
  skipAuth?: boolean
  silent?: boolean
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
