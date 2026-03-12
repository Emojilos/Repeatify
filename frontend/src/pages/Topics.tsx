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
    basic: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    hard: 'bg-red-100 text-red-700',
  }
  const labels: Record<string, string> = {
    basic: 'Базовый',
    medium: 'Средний',
    hard: 'Сложный',
  }
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[level] || 'bg-gray-100 text-gray-600'}`}>
      {labels[level] || level}
    </span>
  )
}

function progressColor(progress: TopicProgress | null): { bg: string; border: string; label: string } {
  if (!progress || progress.total_attempts === 0) {
    return { bg: 'bg-white', border: 'border-gray-200', label: 'Не начато' }
  }
  const strength = progress.strength_score
  if (strength >= 0.7) {
    return { bg: 'bg-green-50', border: 'border-green-300', label: 'Изучено' }
  }
  return { bg: 'bg-yellow-50', border: 'border-yellow-300', label: 'В процессе' }
}

function TopicCard({ topic }: { topic: Topic }) {
  const { bg, border, label } = progressColor(topic.user_progress)

  return (
    <Link
      to={`/topics/${topic.id}`}
      className={`block rounded-xl border ${border} ${bg} p-4 transition-shadow hover:shadow-md`}
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
          {topic.task_number}
        </span>
        <div className="flex items-center gap-2">
          {difficultyBadge(topic.difficulty_level)}
          <span className="text-xs font-medium text-gray-500">
            {topic.max_points} {topic.max_points === 1 ? 'балл' : topic.max_points < 5 ? 'балла' : 'баллов'}
          </span>
        </div>
      </div>
      <h3 className="mb-1 text-sm font-semibold text-gray-900">{topic.title}</h3>
      {topic.description && (
        <p className="mb-2 line-clamp-2 text-xs text-gray-500">{topic.description}</p>
      )}
      <div className="flex items-center justify-between">
        <span className={`text-xs font-medium ${
          label === 'Изучено' ? 'text-green-600' :
          label === 'В процессе' ? 'text-yellow-600' :
          'text-gray-400'
        }`}>
          {label}
        </span>
        {topic.user_progress && topic.user_progress.fire_completed && (
          <span className="text-xs" title="FIRe пройден">🔥</span>
        )}
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
        <h1 className="mb-6 text-2xl font-bold">Темы</h1>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-36 animate-pulse rounded-xl border border-gray-200 bg-gray-100" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-4 text-2xl font-bold">Темы</h1>
        <p className="text-red-600">Ошибка загрузки: {error}</p>
      </div>
    )
  }

  const part1 = topics.filter((t) => t.task_number <= 12)
  const part2 = topics.filter((t) => t.task_number >= 13)

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold">Темы ЕГЭ по математике</h1>

      <section className="mb-8">
        <h2 className="mb-4 text-lg font-semibold text-gray-700">
          Часть 1 <span className="text-sm font-normal text-gray-400">— задания 1–12, по 1 баллу</span>
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {part1.map((topic) => (
            <TopicCard key={topic.id} topic={topic} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-700">
          Часть 2 <span className="text-sm font-normal text-gray-400">— задания 13–19, 2–4 балла</span>
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
