import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import MathRenderer from '../components/MathRenderer'
import ProblemContent from '../components/ProblemContent'

interface TopicProgress {
  strength_score: number
  fire_completed: boolean
  fire_completed_at: string | null
  total_attempts: number
  correct_attempts: number
  last_practiced_at: string | null
}

interface TopicDetail {
  id: string
  task_number: number
  title: string
  description: string | null
  difficulty_level: string
  max_points: number
  estimated_study_hours: number | null
  order_index: number
  parent_topic_id: string | null
  user_progress: TopicProgress | null
}

interface ProblemSubcategory {
  name: string
  count: number
  sample_problem_text: string | null
  sample_problem_images?: string[] | null
}

interface ProblemSubcategoryListResponse {
  items: ProblemSubcategory[]
  total: number
}

interface TopicRelationship {
  id: string
  source_topic_id: string
  target_topic_id: string
  relationship_type: string
  description: string | null
  related_topic: {
    id: string
    task_number: number
    title: string
  } | null
}

function difficultyBadge(level: string) {
  const styles: Record<string, string> = {
    basic: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    easy: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
    hard: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    olympiad: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  }
  const labels: Record<string, string> = {
    basic: 'Базовый',
    easy: 'Легко',
    medium: 'Средний',
    hard: 'Сложный',
    olympiad: 'Олимпиадный',
  }
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[level] || 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}`}>
      {labels[level] || level}
    </span>
  )
}

function strengthLabel(progress: TopicProgress | null): { text: string; color: string } {
  if (!progress || progress.total_attempts === 0) {
    return { text: 'Не начато', color: 'text-gray-400 dark:text-gray-500' }
  }
  const s = progress.strength_score
  if (s >= 0.7) return { text: `${Math.round(s * 100)}% — Изучено`, color: 'text-green-600' }
  if (s >= 0.3) return { text: `${Math.round(s * 100)}% — В процессе`, color: 'text-yellow-600' }
  return { text: `${Math.round(s * 100)}% — Начато`, color: 'text-red-500' }
}

export default function TopicDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [topic, setTopic] = useState<TopicDetail | null>(null)
  const [relationships, setRelationships] = useState<TopicRelationship[]>([])
  const [subcategories, setSubcategories] = useState<ProblemSubcategory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return

    setLoading(true)
    setError(null)

    Promise.all([
      api<TopicDetail>(`/api/topics/${id}`),
      api<TopicRelationship[]>(`/api/topics/${id}/relationships`),
      api<ProblemSubcategoryListResponse>(`/api/problems/subcategories?topic_id=${id}`),
    ])
      .then(([topicData, relData, subcategoryData]) => {
        setTopic(topicData)
        setRelationships(relData)
        setSubcategories(subcategoryData.items)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  const totalProblemCount = subcategories.reduce((sum, item) => sum + item.count, 0)

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-4 h-8 w-64 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="mb-6 h-4 w-96 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="mb-8 h-40 animate-pulse rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !topic) {
    return (
      <div className="p-8">
        <Link to="/topics" className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline">
          &larr; Все темы
        </Link>
        <p className="mt-4 text-red-600">Ошибка загрузки: {error || 'Тема не найдена'}</p>
      </div>
    )
  }

  const strength = strengthLabel(topic.user_progress)
  const accuracy = topic.user_progress && topic.user_progress.total_attempts > 0
    ? Math.round((topic.user_progress.correct_attempts / topic.user_progress.total_attempts) * 100)
    : null

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Back link */}
      <Link to="/topics" className="mb-5 inline-flex items-center text-sm font-medium text-gray-500 transition-colors hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
        Все задания
      </Link>

      {/* Topic header */}
      <div className="mb-7">
        <div className="mb-3 flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gray-950 text-lg font-bold text-white dark:bg-white dark:text-gray-950">
            {topic.task_number}
          </span>
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500">Задание ЕГЭ</div>
            <h1 className="text-2xl font-semibold tracking-tight text-gray-950 dark:text-gray-50">{topic.title}</h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm">
          {difficultyBadge(topic.difficulty_level)}
          <span className="text-gray-500 dark:text-gray-400">
            {topic.max_points} {topic.max_points === 1 ? 'балл' : topic.max_points < 5 ? 'балла' : 'баллов'}
          </span>
          {topic.estimated_study_hours && (
            <span className="text-gray-400 dark:text-gray-500">~{topic.estimated_study_hours} ч. на изучение</span>
          )}
          <span className={`font-medium ${strength.color}`}>{strength.text}</span>
        </div>
      </div>

      {/* Action buttons */}
      <div className="mb-8 flex flex-wrap gap-3">
        {totalProblemCount > 0 && (
          <Link
            to={`/topics/${topic.id}/practice`}
            className="rounded-xl bg-gray-950 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-gray-800 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-200"
          >
            Решать подборку
          </Link>
        )}
        <Link
          to={`/print?task=${topic.task_number}&count=10`}
          className="rounded-xl border border-gray-200 bg-white px-5 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300 dark:hover:border-gray-700 dark:hover:bg-gray-800"
        >
          Распечатать задания
        </Link>
      </div>

      {/* User progress stats */}
      {topic.user_progress && topic.user_progress.total_attempts > 0 && (
        <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-white p-4 text-center dark:border-gray-700 dark:bg-gray-800">
            <div className="text-2xl font-bold text-blue-600">{topic.user_progress.total_attempts}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Попыток</div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4 text-center dark:border-gray-700 dark:bg-gray-800">
            <div className="text-2xl font-bold text-green-600">{topic.user_progress.correct_attempts}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Правильных</div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4 text-center dark:border-gray-700 dark:bg-gray-800">
            <div className="text-2xl font-bold text-yellow-600">{accuracy !== null ? `${accuracy}%` : '—'}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Точность</div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4 text-center dark:border-gray-700 dark:bg-gray-800">
            <div className="text-2xl font-bold text-purple-600">{Math.round(topic.user_progress.strength_score * 100)}%</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Сила темы</div>
          </div>
        </div>
      )}

      {/* Theory section */}
      {topic.description && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-gray-100">Обзор</h2>
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <MathRenderer content={topic.description} />
          </div>
        </section>
      )}

      {/* Subcategories section */}
      {subcategories.length > 0 && (
        <section className="mb-8">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Подкатегории
              </h2>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Откройте подкатегорию, чтобы выбрать конкретное задание или решать всю подборку.
              </p>
            </div>
            <div className="text-sm font-medium text-gray-400 dark:text-gray-500">
              {totalProblemCount} заданий
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {subcategories.map((subcategory) => (
              <Link
                key={subcategory.name}
                to={`/topics/${topic.id}/subcategory?name=${encodeURIComponent(subcategory.name)}`}
                className="group flex min-h-56 flex-col rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-gray-400 hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-gray-600 dark:hover:bg-gray-800"
              >
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gray-950 text-sm font-semibold text-white dark:bg-white dark:text-gray-950">
                    {topic.task_number}
                  </div>
                  <span className="rounded-full border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold text-gray-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400">
                    {subcategory.count} заданий
                  </span>
                </div>

                <h3 className="mb-3 text-base font-semibold leading-snug text-gray-950 dark:text-gray-50">
                  {subcategory.name}
                </h3>

                {subcategory.sample_problem_text ? (
                  <div className="line-clamp-3 text-sm leading-relaxed text-gray-500 dark:text-gray-400">
                    <ProblemContent
                      text={subcategory.sample_problem_text}
                      images={subcategory.sample_problem_images}
                      imageClassName="h-6 w-auto rounded bg-white p-0.5 dark:invert"
                    />
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 dark:text-gray-400">Задания этой подкатегории.</p>
                )}

                <div className="mt-auto pt-5 text-sm font-semibold text-gray-300 transition group-hover:text-gray-900 dark:text-gray-600 dark:group-hover:text-gray-100">
                  Открыть подкатегорию
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Related topics */}
      {relationships.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">Связанные темы</h2>
          <div className="flex flex-wrap gap-2">
            {relationships.map((rel) => (
              rel.related_topic && (
                <Link
                  key={rel.id}
                  to={`/topics/${rel.related_topic.id}`}
                  className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm transition-colors hover:border-blue-300 hover:bg-blue-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-700 dark:hover:bg-blue-900/30"
                >
                  <span className="mr-1.5 font-semibold text-blue-600">#{rel.related_topic.task_number}</span>
                  <span className="text-gray-700 dark:text-gray-300">{rel.related_topic.title}</span>
                  {rel.relationship_type === 'prerequisite' && (
                    <span className="ml-1.5 text-xs text-gray-400 dark:text-gray-500">(пререквизит)</span>
                  )}
                </Link>
              )
            ))}
          </div>
        </section>
      )}

      {subcategories.length === 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">Задания</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">Задания по этой теме пока не добавлены.</p>
        </section>
      )}
    </div>
  )
}
