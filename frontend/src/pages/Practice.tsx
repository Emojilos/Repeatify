import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSessionStore } from '../stores/sessionStore'

export default function Practice() {
  const { totalDue, loading, error, fetchSession } = useSessionStore()
  const navigate = useNavigate()

  useEffect(() => {
    fetchSession()
  }, [fetchSession])

  const handleStart = () => {
    navigate('/practice/session')
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-6 h-8 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="mx-auto max-w-md">
          <div className="h-48 animate-pulse rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500">Повторение</div>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-gray-950 dark:text-gray-50">Тренировка</h1>
      </div>

      <div className="mx-auto max-w-md">
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm dark:border-gray-800 dark:bg-gray-900">
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
              {error}
            </div>
          )}

          {totalDue > 0 ? (
            <>
              <div className="mb-2 text-6xl font-bold text-blue-600">{totalDue}</div>
              <div className="mb-6 text-gray-500 dark:text-gray-400">
                {totalDue === 1
                  ? 'карточка на повторение'
                  : totalDue < 5
                    ? 'карточки на повторение'
                    : 'карточек на повторение'}
              </div>
              <button
                onClick={handleStart}
                className="w-full rounded-xl bg-gray-950 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-gray-800 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-200"
              >
                Начать тренировку
              </button>
            </>
          ) : (
            <>
              <div className="mb-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
                Нет карточек на повторение
              </div>
              <div className="mb-6 text-sm text-gray-500 dark:text-gray-400">
                Отличная работа! Все карточки повторены. Решайте новые задания, чтобы добавить карточки.
              </div>
              <Link
                to="/topics"
                className="inline-block rounded-xl bg-gray-950 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-gray-800 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-200"
              >
                К темам
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
