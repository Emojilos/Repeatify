import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

interface TopicProgress {
  strength_score: number
  fire_completed: boolean
  total_attempts: number
  correct_attempts: number
}

interface Topic {
  id: string
  task_number: number
  title: string
  description: string | null
  difficulty_level: string
  max_points: number
  estimated_study_hours: number | null
  user_progress: TopicProgress | null
}

function difficultyBadge(level: string) {
  const styles: Record<string, string> = {
    basic: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/30 dark:text-emerald-300',
    medium: 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/70 dark:bg-amber-950/30 dark:text-amber-300',
    hard: 'border-red-200 bg-red-50 text-red-700 dark:border-red-900/70 dark:bg-red-950/30 dark:text-red-300',
  }
  const labels: Record<string, string> = {
    basic: 'Базовый',
    medium: 'Средний',
    hard: 'Сложный',
  }
  return (
    <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${styles[level] || 'border-gray-200 bg-white text-gray-600 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400'}`}>
      {labels[level] || level}
    </span>
  )
}

function progressColor(progress: TopicProgress | null): { border: string; label: string } {
  if (!progress || progress.total_attempts === 0) {
    return { border: 'border-gray-200 dark:border-gray-800', label: 'Не начато' }
  }
  const strength = progress.strength_score
  if (strength >= 0.7) {
    return { border: 'border-gray-300 dark:border-gray-700', label: 'Изучено' }
  }
  return { border: 'border-gray-300 dark:border-gray-700', label: 'В процессе' }
}

function TopicCard({ topic }: { topic: Topic }) {
  const { border, label } = progressColor(topic.user_progress)

  return (
    <Link
      to={`/topics/${topic.id}`}
      className={`group block rounded-2xl border ${border} bg-white p-5 shadow-sm transition hover:border-gray-400 hover:bg-gray-50 dark:bg-gray-900 dark:hover:border-gray-600 dark:hover:bg-gray-800`}
    >
      <div className="mb-5 flex items-center justify-between gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-950 text-sm font-semibold text-white dark:bg-white dark:text-gray-950">
          {topic.task_number}
        </span>
        <div className="flex min-w-0 flex-wrap items-center justify-end gap-2">
          {difficultyBadge(topic.difficulty_level)}
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
            {topic.max_points} {topic.max_points === 1 ? 'балл' : topic.max_points < 5 ? 'балла' : 'баллов'}
          </span>
        </div>
      </div>
      <h3 className="mb-2 text-base font-semibold leading-snug text-gray-950 dark:text-gray-50">{topic.title}</h3>
      {topic.description && (
        <p className="mb-5 line-clamp-2 text-sm leading-relaxed text-gray-500 dark:text-gray-400">{topic.description}</p>
      )}
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-400 dark:text-gray-500">
          {label}
        </span>
        <span className="text-xs font-semibold text-gray-300 transition group-hover:text-gray-900 dark:text-gray-600 dark:group-hover:text-gray-100">
          Открыть
        </span>
      </div>
    </Link>
  )
}

export default function Topics() {
  const [topics, setTopics] = useState<Topic[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api<Topic[]>('/api/topics')
      .then(setTopics)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-2xl font-semibold tracking-tight text-gray-950 dark:text-gray-50">Задания ЕГЭ</h1>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-36 animate-pulse rounded-xl border border-gray-200 bg-gray-100 dark:border-gray-700 dark:bg-gray-800" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-4 text-2xl font-semibold tracking-tight text-gray-950 dark:text-gray-50">Задания ЕГЭ</h1>
        <p className="text-red-600">Ошибка загрузки: {error}</p>
      </div>
    )
  }

  const part1 = topics.filter((t) => t.task_number <= 12)
  const part2 = topics.filter((t) => t.task_number >= 13)

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500">Банк заданий</div>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-gray-950 dark:text-gray-50">ЕГЭ по математике</h1>
      </div>

      <section className="mb-8">
        <h2 className="mb-4 text-lg font-semibold text-gray-800 dark:text-gray-200">
          Часть 1 <span className="text-sm font-normal text-gray-400 dark:text-gray-500">— задания 1–12, по 1 баллу</span>
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {part1.map((topic) => (
            <TopicCard key={topic.id} topic={topic} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-800 dark:text-gray-200">
          Часть 2 <span className="text-sm font-normal text-gray-400 dark:text-gray-500">— задания 13–19, 2–4 балла</span>
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {part2.map((topic) => (
            <TopicCard key={topic.id} topic={topic} />
          ))}
        </div>
      </section>
    </div>
  )
}
