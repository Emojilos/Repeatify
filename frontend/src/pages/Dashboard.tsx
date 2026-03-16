import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

interface TopicProgress {
  task_number: number
  title: string
  strength_score: number
  fire_completed: boolean
}

interface WeeklyStats {
  problems_solved: number
  problems_correct: number
}

interface DashboardData {
  exam_countdown: number | null
  topics_progress: TopicProgress[]
  today_review_count: number
  weekly_stats: WeeklyStats
  recommendations: string[]
  current_xp: number
  current_level: number
  current_streak: number
}

interface DailyTask {
  task_type: string
  task_number: number | null
  prototype_id: string | null
  title: string
  estimated_minutes: number | null
}

interface TodayData {
  review_cards_due: number
  new_material: DailyTask[]
  total_estimated_minutes: number | null
}

function strengthColor(strength: number): string {
  if (strength >= 0.7) return 'bg-green-500'
  if (strength >= 0.4) return 'bg-yellow-500'
  if (strength > 0) return 'bg-orange-500'
  return 'bg-gray-300 dark:bg-gray-600'
}

function strengthBorder(strength: number): string {
  if (strength >= 0.7) return 'border-green-400'
  if (strength >= 0.4) return 'border-yellow-400'
  if (strength > 0) return 'border-orange-400'
  return 'border-gray-200 dark:border-gray-700'
}

function strengthBg(strength: number): string {
  if (strength >= 0.7) return 'bg-green-50 dark:bg-green-900/30'
  if (strength >= 0.4) return 'bg-yellow-50 dark:bg-yellow-900/30'
  if (strength > 0) return 'bg-orange-50 dark:bg-orange-900/30'
  return 'bg-white dark:bg-gray-800'
}

function pluralDays(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return `${n} день`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${n} дня`
  return `${n} дней`
}

function pluralCards(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return `${n} карточка`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${n} карточки`
  return `${n} карточек`
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [today, setToday] = useState<TodayData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api<DashboardData>('/api/progress/dashboard'),
      api<TodayData>('/api/study-plan/today').catch(() => null),
    ])
      .then(([dashData, todayData]) => {
        setData(dashData)
        setToday(todayData)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-8 h-32 animate-pulse rounded-2xl bg-gray-100 dark:bg-gray-800" />
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-4 text-2xl font-bold dark:text-gray-100">Dashboard</h1>
        <p className="text-red-600">Ошибка загрузки: {error}</p>
      </div>
    )
  }

  if (!data) return null

  const weeklyAccuracy = data.weekly_stats.problems_solved > 0
    ? Math.round((data.weekly_stats.problems_correct / data.weekly_stats.problems_solved) * 100)
    : 0

  const isNewUser = data.current_xp === 0
    && data.weekly_stats.problems_solved === 0
    && data.topics_progress.every((t) => t.strength_score === 0 && !t.fire_completed)

  return (
    <div className="p-8">
      {/* New user welcome */}
      {isNewUser && (
        <div className="mb-8 rounded-2xl border border-indigo-200 bg-gradient-to-r from-indigo-50 to-blue-50 p-6 dark:border-indigo-800 dark:from-indigo-900/30 dark:to-blue-900/30">
          <h2 className="mb-2 text-lg font-bold text-indigo-900 dark:text-indigo-100">
            Добро пожаловать в Repeatify!
          </h2>
          <p className="mb-4 text-sm text-indigo-700 dark:text-indigo-300">
            Начните с изучения первой темы. Пройдите FIRe-flow, чтобы разобрать теорию, а затем закрепите знания на практике.
          </p>
          <Link
            to="/topics"
            className="inline-block rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700"
          >
            Перейти к темам
          </Link>
        </div>
      )}

      {/* Exam countdown */}
      {data.exam_countdown !== null ? (
        <div className="mb-8 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-100">До экзамена осталось</p>
              <p className="text-5xl font-bold">{pluralDays(data.exam_countdown)}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-blue-100">Уровень {data.current_level}</p>
              <p className="text-2xl font-bold">{data.current_xp} XP</p>
              {data.current_streak > 0 && (
                <p className="mt-1 text-sm text-blue-100">
                  Серия: {data.current_streak} {data.current_streak === 1 ? 'день' : data.current_streak < 5 ? 'дня' : 'дней'}
                </p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="mb-8 rounded-2xl border border-blue-200 bg-blue-50 p-6 dark:border-blue-800 dark:bg-blue-900/30">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            Установите дату экзамена в{' '}
            <Link to="/profile" className="font-medium underline">профиле</Link>
            , чтобы видеть обратный отсчёт и получать персональные рекомендации.
          </p>
        </div>
      )}

      {/* Stats row */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* SRS widget */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p className="mb-1 text-sm font-medium text-gray-500 dark:text-gray-400">Сегодня на повторение</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{pluralCards(data.today_review_count)}</p>
          {data.today_review_count > 0 ? (
            <Link
              to="/practice"
              className="mt-3 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              Начать повторение
            </Link>
          ) : (
            <p className="mt-2 text-sm text-green-600">Все карточки повторены!</p>
          )}
        </div>

        {/* Weekly stats */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p className="mb-1 text-sm font-medium text-gray-500 dark:text-gray-400">За неделю</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{data.weekly_stats.problems_solved}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data.weekly_stats.problems_solved > 0
              ? `задач решено, ${weeklyAccuracy}% правильно`
              : 'задач решено'}
          </p>
        </div>

        {/* Streak */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <p className="mb-1 text-sm font-medium text-gray-500 dark:text-gray-400">Серия</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {data.current_streak} {data.current_streak === 1 ? 'день' : data.current_streak < 5 ? 'дня' : 'дней'}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data.current_streak > 0 ? 'Продолжайте заниматься!' : 'Решите задание, чтобы начать серию'}
          </p>
        </div>
      </div>

      {/* Today section */}
      {today ? (
        <div className="mb-8">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">Сегодня</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Review block */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-2 flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100 text-lg dark:bg-purple-900/50">
                  🔄
                </span>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">Повторение FSRS</h3>
              </div>
              {today.review_cards_due > 0 ? (
                <>
                  <p className="mb-3 text-sm text-gray-600 dark:text-gray-400">
                    {pluralCards(today.review_cards_due)} на повторение
                  </p>
                  <Link
                    to="/practice"
                    className="inline-block rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700"
                  >
                    Начать повторение
                  </Link>
                </>
              ) : (
                <p className="text-sm text-green-600 dark:text-green-400">Все карточки повторены!</p>
              )}
            </div>

            {/* New material block */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-2 flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-lg dark:bg-blue-900/50">
                  📖
                </span>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">Новый материал</h3>
              </div>
              {today.new_material.length > 0 ? (
                <div className="space-y-2">
                  {today.new_material.map((task, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {task.task_number && (
                          <span className="flex h-6 w-6 items-center justify-center rounded bg-blue-600 text-[10px] font-bold text-white">
                            {task.task_number}
                          </span>
                        )}
                        <span className="text-sm text-gray-700 dark:text-gray-300">{task.title}</span>
                      </div>
                      {task.estimated_minutes != null && task.estimated_minutes > 0 && (
                        <span className="text-xs text-gray-400">{task.estimated_minutes} мин</span>
                      )}
                    </div>
                  ))}
                  {today.new_material[0]?.task_number && (
                    <Link
                      to="/topics"
                      className="mt-2 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                    >
                      Изучить
                    </Link>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-500 dark:text-gray-400">На сегодня новых тем нет</p>
              )}
            </div>
          </div>
          {today.total_estimated_minutes != null && today.total_estimated_minutes > 0 && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Примерное время: ~{today.total_estimated_minutes} мин
            </p>
          )}
        </div>
      ) : !isNewUser && (
        <div className="mb-8 rounded-xl border border-indigo-200 bg-indigo-50 p-5 dark:border-indigo-800 dark:bg-indigo-900/30">
          <h2 className="mb-2 font-semibold text-indigo-900 dark:text-indigo-100">Персональный план</h2>
          <p className="mb-3 text-sm text-indigo-700 dark:text-indigo-300">
            Создайте персональный план подготовки, чтобы видеть ежедневные задачи.
          </p>
          <Link
            to="/onboarding"
            className="inline-block rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700"
          >
            Создать план
          </Link>
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <div className="mb-8 rounded-xl border border-amber-200 bg-amber-50 p-5 dark:border-amber-800 dark:bg-amber-900/30">
          <h2 className="mb-3 text-sm font-semibold text-amber-800 dark:text-amber-200">Рекомендации</h2>
          <ul className="space-y-1.5">
            {data.recommendations.map((rec, i) => (
              <li key={i} className="text-sm text-amber-700 dark:text-amber-300">
                &bull; {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Topics progress map */}
      <div className="mb-4">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">Карта тем</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7">
          {data.topics_progress.map((topic) => (
            <Link
              key={topic.task_number}
              to="/topics"
              className={`rounded-xl border ${strengthBorder(topic.strength_score)} ${strengthBg(topic.strength_score)} p-3 transition-shadow hover:shadow-md`}
            >
              <div className="mb-2 flex items-center justify-between">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-xs font-bold text-white">
                  {topic.task_number}
                </span>
                {topic.fire_completed && (
                  <span className="text-xs" title="FIRe пройден">🔥</span>
                )}
              </div>
              <p className="mb-2 line-clamp-2 text-xs font-medium text-gray-800 dark:text-gray-200">{topic.title}</p>
              <div className="h-1.5 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className={`h-full rounded-full ${strengthColor(topic.strength_score)} transition-all`}
                  style={{ width: `${Math.round(topic.strength_score * 100)}%` }}
                />
              </div>
              <p className="mt-1 text-right text-[10px] text-gray-500 dark:text-gray-400">
                {Math.round(topic.strength_score * 100)}%
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
