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

function strengthColor(strength: number): string {
  if (strength >= 0.7) return 'bg-green-500'
  if (strength >= 0.4) return 'bg-yellow-500'
  if (strength > 0) return 'bg-orange-500'
  return 'bg-gray-300'
}

function strengthBorder(strength: number): string {
  if (strength >= 0.7) return 'border-green-400'
  if (strength >= 0.4) return 'border-yellow-400'
  if (strength > 0) return 'border-orange-400'
  return 'border-gray-200'
}

function strengthBg(strength: number): string {
  if (strength >= 0.7) return 'bg-green-50'
  if (strength >= 0.4) return 'bg-yellow-50'
  if (strength > 0) return 'bg-orange-50'
  return 'bg-white'
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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api<DashboardData>('/api/progress/dashboard')
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-8 h-32 animate-pulse rounded-2xl bg-gray-100" />
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-4 text-2xl font-bold">Dashboard</h1>
        <p className="text-red-600">Ошибка загрузки: {error}</p>
      </div>
    )
  }

  if (!data) return null

  const weeklyAccuracy = data.weekly_stats.problems_solved > 0
    ? Math.round((data.weekly_stats.problems_correct / data.weekly_stats.problems_solved) * 100)
    : 0

  return (
    <div className="p-8">
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
        <div className="mb-8 rounded-2xl border border-blue-200 bg-blue-50 p-6">
          <p className="text-sm text-blue-700">
            Установите дату экзамена в{' '}
            <Link to="/profile" className="font-medium underline">профиле</Link>
            , чтобы видеть обратный отсчёт и получать персональные рекомендации.
          </p>
        </div>
      )}

      {/* Stats row */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* SRS widget */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="mb-1 text-sm font-medium text-gray-500">Сегодня на повторение</p>
          <p className="text-3xl font-bold text-gray-900">{pluralCards(data.today_review_count)}</p>
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
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="mb-1 text-sm font-medium text-gray-500">За неделю</p>
          <p className="text-3xl font-bold text-gray-900">{data.weekly_stats.problems_solved}</p>
          <p className="text-sm text-gray-500">
            {data.weekly_stats.problems_solved > 0
              ? `задач решено, ${weeklyAccuracy}% правильно`
              : 'задач решено'}
          </p>
        </div>

        {/* Streak */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="mb-1 text-sm font-medium text-gray-500">Серия</p>
          <p className="text-3xl font-bold text-gray-900">
            {data.current_streak} {data.current_streak === 1 ? 'день' : data.current_streak < 5 ? 'дня' : 'дней'}
          </p>
          <p className="text-sm text-gray-500">
            {data.current_streak > 0 ? 'Продолжайте заниматься!' : 'Решите задание, чтобы начать серию'}
          </p>
        </div>
      </div>

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <div className="mb-8 rounded-xl border border-amber-200 bg-amber-50 p-5">
          <h2 className="mb-3 text-sm font-semibold text-amber-800">Рекомендации</h2>
          <ul className="space-y-1.5">
            {data.recommendations.map((rec, i) => (
              <li key={i} className="text-sm text-amber-700">
                &bull; {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Topics progress map */}
      <div className="mb-4">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Карта тем</h2>
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
              <p className="mb-2 line-clamp-2 text-xs font-medium text-gray-800">{topic.title}</p>
              <div className="h-1.5 overflow-hidden rounded-full bg-gray-200">
                <div
                  className={`h-full rounded-full ${strengthColor(topic.strength_score)} transition-all`}
                  style={{ width: `${Math.round(topic.strength_score * 100)}%` }}
                />
              </div>
              <p className="mt-1 text-right text-[10px] text-gray-500">
                {Math.round(topic.strength_score * 100)}%
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
