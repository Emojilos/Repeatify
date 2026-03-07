import { useState } from 'react'
import { Link } from 'react-router-dom'
import { signUp } from '../../services/supabase/auth.service.js'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    if (password !== confirm) {
      setError('Пароли не совпадают')
      return
    }
    if (password.length < 6) {
      setError('Пароль должен содержать минимум 6 символов')
      return
    }

    setLoading(true)
    try {
      await signUp(email, password)
      setSuccess(true)
    } catch (err) {
      setError(err.message || 'Ошибка регистрации')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white shadow rounded-xl p-8 text-center space-y-4">
          <div className="text-5xl">📧</div>
          <h2 className="text-xl font-bold text-gray-900">Проверьте почту</h2>
          <p className="text-gray-600 text-sm">
            Мы отправили письмо на <strong>{email}</strong>. Перейдите по ссылке в письме, чтобы
            подтвердить аккаунт.
          </p>
          <Link
            to="/login"
            className="inline-block mt-4 text-blue-600 hover:underline font-medium text-sm"
          >
            Перейти ко входу
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 text-center">Repeatify</h1>
          <h2 className="mt-2 text-center text-lg text-gray-600">Создать аккаунт</h2>
        </div>

        <form className="bg-white shadow rounded-xl p-8 space-y-5" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="password">
              Пароль
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Минимум 6 символов"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="confirm">
              Повтор пароля
            </label>
            <input
              id="confirm"
              type="password"
              autoComplete="new-password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            {loading ? 'Создаю аккаунт...' : 'Зарегистрироваться'}
          </button>

          <p className="text-center text-sm text-gray-600">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="text-blue-600 hover:underline font-medium">
              Войти
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
