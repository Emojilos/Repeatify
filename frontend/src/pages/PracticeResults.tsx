import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useSessionStore } from '../stores/sessionStore'

export default function PracticeResults() {
  const { results, cards, reset } = useSessionStore()

  const stats = useMemo(() => {
    const total = results.length
    const correct = results.filter((r) => r.review.is_correct).length
    const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0
    const totalXp = results.reduce((sum, r) => sum + r.review.xp_earned, 0)

    // Group by topic
    const byTopic = new Map<string, { title: string; correct: number; total: number }>()
    for (const r of results) {
      const topicId = r.card.topic_id
      const title = r.card.topic_title || `Задание ${r.card.task_number}`
      const entry = byTopic.get(topicId) || { title, correct: 0, total: 0 }
      entry.total++
      if (r.review.is_correct) entry.correct++
      byTopic.set(topicId, entry)
    }

    return { total, correct, accuracy, totalXp, byTopic: Array.from(byTopic.values()) }
  }, [results])

  // If no results (direct navigation), show empty state
  if (results.length === 0 && cards.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="mb-4 text-gray-500 dark:text-gray-400">Нет данных о сессии</p>
        <Link
          to="/practice"
          className="inline-block rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
        >
          Начать тренировку
        </Link>
      </div>
    )
  }

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">Результаты сессии</h1>

      <div className="mx-auto max-w-lg">
        {/* Summary card */}
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 text-center dark:border-gray-700 dark:bg-gray-800">
          {/* XP earned */}
          {stats.totalXp > 0 && (
            <div className="mb-4 animate-bounce text-3xl font-bold text-yellow-500">
              +{stats.totalXp} XP
            </div>
          )}

          {/* Stats grid */}
          <div className="mb-4 grid grid-cols-3 gap-4">
            <div>
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.total}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Решено</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{stats.correct}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Правильно</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">{stats.accuracy}%</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Точность</div>
            </div>
          </div>

          {/* Accuracy bar */}
          <div className="h-3 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
            <div
              className="h-full rounded-full bg-green-500 transition-all duration-500"
              style={{ width: `${stats.accuracy}%` }}
            />
          </div>
        </div>

        {/* Topic breakdown */}
        {stats.byTopic.length > 0 && (
          <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            <h2 className="mb-4 text-sm font-semibold text-gray-700 dark:text-gray-300">По темам</h2>
            <div className="space-y-3">
              {stats.byTopic.map((topic) => (
                <div key={topic.title} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300">{topic.title}</span>
                  <span className="text-sm font-medium">
                    <span className={topic.correct === topic.total ? 'text-green-600' : 'text-gray-900 dark:text-gray-100'}>
                      {topic.correct}/{topic.total}
                    </span>
                    <span className="ml-1 text-gray-400 dark:text-gray-500">правильно</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Navigation buttons */}
        <div className="flex gap-3">
          <Link
            to="/practice"
            onClick={() => reset()}
            className="flex-1 rounded-lg bg-blue-600 px-6 py-3 text-center text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Ещё одна сессия
          </Link>
          <Link
            to="/dashboard"
            onClick={() => reset()}
            className="flex-1 rounded-lg border border-gray-300 bg-white px-6 py-3 text-center text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            На главную
          </Link>
        </div>
      </div>
    </div>
  )
}
