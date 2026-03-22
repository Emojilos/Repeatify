import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

const TARGET_OPTIONS: { value: number; label: string; description: string }[] = [
  { value: 70, label: '70 баллов', description: 'Идеальная Часть 1' },
  { value: 80, label: '80 баллов', description: 'Джентльменский набор' },
  { value: 90, label: '90 баллов', description: '+ Геометрия и параметры' },
  { value: 100, label: '100 баллов', description: 'Максимум' },
]

export default function Onboarding() {
  const navigate = useNavigate()
  const loadUser = useAuthStore((s) => s.loadUser)

  const [targetScore, setTargetScore] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleFinish() {
    if (!targetScore) return
    setSaving(true)
    setError(null)
    try {
      await api('/api/users/me', {
        method: 'PATCH',
        body: JSON.stringify({ target_score: targetScore }),
      })

      // Generate the knowledge map plan
      await api('/api/study-plan/generate', {
        method: 'POST',
        body: JSON.stringify({ target_score: targetScore }),
      })

      await loadUser()
      navigate('/plan')
    } catch {
      setError('Не удалось сохранить настройки. Попробуйте ещё раз.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Добро пожаловать в Repeatify
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Выберите целевой балл ЕГЭ
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 sm:p-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Какой балл вы хотите получить?
          </h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
            Мы покажем, какие задания нужно освоить для достижения цели
          </p>
          <div className="grid grid-cols-1 gap-3">
            {TARGET_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setTargetScore(opt.value)}
                className={`p-4 rounded-xl border-2 text-left transition-all ${
                  targetScore === opt.value
                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/30 dark:border-blue-500'
                    : 'border-gray-200 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-700'
                }`}
              >
                <span className="text-lg font-semibold text-gray-900 dark:text-white">
                  {opt.label}
                </span>
                <span className="block text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  {opt.description}
                </span>
              </button>
            ))}
          </div>

          {error && (
            <p className="text-red-600 dark:text-red-400 text-sm mt-4">
              {error}
            </p>
          )}

          <div className="mt-8">
            <button
              onClick={handleFinish}
              disabled={!targetScore || saving}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? 'Сохранение...' : 'Начать подготовку'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
