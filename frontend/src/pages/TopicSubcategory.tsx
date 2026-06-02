import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import ProblemContent from '../components/ProblemContent'

interface TopicInfo {
  id: string
  task_number: number
  title: string
  difficulty_level: string
  max_points: number
}

interface Problem {
  id: string
  topic_id: string
  task_number: number
  difficulty: string
  problem_text: string
  problem_images?: string[] | null
  max_points?: number | null
  subcategory?: string | null
}

interface ProblemListResponse {
  items: Problem[]
  total: number
  page: number
  page_size: number
}

function difficultyBadge(level: string) {
  const styles: Record<string, string> = {
    basic: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/30 dark:text-emerald-300',
    easy: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/30 dark:text-emerald-300',
    medium: 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/70 dark:bg-amber-950/30 dark:text-amber-300',
    hard: 'border-red-200 bg-red-50 text-red-700 dark:border-red-900/70 dark:bg-red-950/30 dark:text-red-300',
    olympiad: 'border-violet-200 bg-violet-50 text-violet-700 dark:border-violet-900/70 dark:bg-violet-950/30 dark:text-violet-300',
  }
  const labels: Record<string, string> = {
    basic: 'Базовый',
    easy: 'Базовый',
    medium: 'Средний',
    hard: 'Сложный',
    olympiad: 'Олимпиадный',
  }

  return (
    <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${styles[level] || 'border-gray-200 bg-white text-gray-600 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400'}`}>
      {labels[level] || level}
    </span>
  )
}

export default function TopicSubcategory() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const subcategory = searchParams.get('name') || ''

  const [topic, setTopic] = useState<TopicInfo | null>(null)
  const [problems, setProblems] = useState<Problem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id || !subcategory) {
      setError('Подкатегория не выбрана')
      setLoading(false)
      return
    }

    let cancelled = false

    async function loadSubcategory() {
      setLoading(true)
      setError(null)

      try {
        const pageSize = 100
        let page = 1
        let total = 0
        const items: Problem[] = []
        const encodedSubcategory = encodeURIComponent(subcategory)

        const [topicData] = await Promise.all([
          api<TopicInfo>(`/api/topics/${id}`),
          (async () => {
            do {
              const data = await api<ProblemListResponse>(
                `/api/problems?topic_id=${id}&subcategory=${encodedSubcategory}&page=${page}&page_size=${pageSize}`,
              )
              items.push(...data.items)
              total = data.total
              page += 1
            } while (items.length < total)
          })(),
        ])

        if (!cancelled) {
          setTopic(topicData)
          setProblems(items)
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Ошибка загрузки подкатегории')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadSubcategory()

    return () => {
      cancelled = true
    }
  }, [id, subcategory])

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-5 h-5 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-800" />
        <div className="mb-6 h-28 animate-pulse rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900" />
        <div className="grid gap-3">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="h-28 animate-pulse rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !topic) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        <Link to={id ? `/topics/${id}` : '/topics'} className="text-sm font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
          Назад
        </Link>
        <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
          {error || 'Тема не найдена'}
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <Link to="/topics" className="font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
            Задания
          </Link>
          <span className="text-gray-300 dark:text-gray-700">/</span>
          <Link to={`/topics/${topic.id}`} className="font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
            Задание {topic.task_number}
          </Link>
          <span className="text-gray-300 dark:text-gray-700">/</span>
          <span className="max-w-[42rem] truncate text-gray-500 dark:text-gray-400">{subcategory}</span>
        </div>
        <Link
          to={`/topics/${topic.id}`}
          className="rounded-xl border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-200 dark:hover:border-gray-700 dark:hover:bg-gray-800"
        >
          К подкатегориям
        </Link>
      </div>

      <header className="mb-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="min-w-0">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="rounded-xl bg-gray-950 px-3 py-1.5 text-sm font-semibold text-white dark:bg-white dark:text-gray-950">
                Задание {topic.task_number}
              </span>
              {difficultyBadge(topic.difficulty_level)}
              <span className="rounded-full border border-gray-200 bg-white px-2.5 py-1 text-xs font-medium text-gray-500 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400">
                {problems.length} заданий
              </span>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight text-gray-950 dark:text-gray-50">
              {subcategory}
            </h1>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              Откройте конкретный вариант или решайте подборку последовательно.
            </p>
          </div>

          {problems.length > 0 && (
            <Link
              to={`/topics/${topic.id}/practice?subcategory=${encodeURIComponent(subcategory)}`}
              className="rounded-xl bg-gray-950 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-gray-800 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-200"
            >
              Решать подборку
            </Link>
          )}
        </div>
      </header>

      {problems.length === 0 ? (
        <div className="rounded-2xl border border-gray-200 bg-white p-6 text-sm text-gray-500 shadow-sm dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400">
          В этой подкатегории пока нет задач.
        </div>
      ) : (
        <div className="grid gap-3">
          {problems.map((problem, index) => (
            <Link
              key={problem.id}
              to={`/problems/${problem.id}`}
              className="group block rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-gray-400 hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-gray-600 dark:hover:bg-gray-800"
            >
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                    Вариант {index + 1}
                  </span>
                  {difficultyBadge(problem.difficulty)}
                </div>
                <span className="text-sm font-semibold text-gray-300 transition group-hover:text-gray-900 dark:text-gray-600 dark:group-hover:text-gray-100">
                  Открыть
                </span>
              </div>
              <div className="line-clamp-4 text-base leading-relaxed text-gray-700 dark:text-gray-300">
                <ProblemContent
                  text={problem.problem_text}
                  images={problem.problem_images}
                  imageClassName="h-7 w-auto rounded bg-white p-0.5 dark:invert"
                />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
