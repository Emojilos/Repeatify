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

interface Problem {
  id: string
  topic_id: string
  task_number: number
  difficulty: string
  problem_text: string
  problem_images?: string[] | null
  source: string | null
  max_points: number | null
}

interface ProblemListResponse {
  items: Problem[]
  total: number
  page: number
  page_size: number
}

interface Prototype {
  id: string
  task_number: number
  prototype_code: string
  title: string
  description: string | null
  difficulty_within_task: string
  estimated_study_minutes: number | null
  order_index: number | null
}

interface PrototypeListResponse {
  items: Prototype[]
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
  const [problems, setProblems] = useState<Problem[]>([])
  const [relationships, setRelationships] = useState<TopicRelationship[]>([])
  const [prototypes, setPrototypes] = useState<Prototype[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return

    setLoading(true)
    setError(null)

    Promise.all([
      api<TopicDetail>(`/api/topics/${id}`),
      api<ProblemListResponse>(`/api/problems?topic_id=${id}&page_size=50`),
      api<TopicRelationship[]>(`/api/topics/${id}/relationships`),
    ])
      .then(([topicData, problemsData, relData]) => {
        setTopic(topicData)
        setProblems(problemsData.items)
        setRelationships(relData)
        // Fetch prototypes for this topic's task_number
        return api<PrototypeListResponse>(`/api/prototypes?task_number=${topicData.task_number}`)
      })
      .then((protoData) => {
        setPrototypes(protoData.items)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

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
    <div className="p-8">
      {/* Back link */}
      <Link to="/topics" className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline">
        &larr; Все темы
      </Link>

      {/* Topic header */}
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-lg font-bold text-white">
            {topic.task_number}
          </span>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{topic.title}</h1>
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
          {topic.user_progress?.fire_completed && (
            <span className="text-sm" title="FIRe пройден">🔥 FIRe пройден</span>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="mb-8 flex flex-wrap gap-3">
        <Link
          to={`/topics/${topic.id}/fire`}
          className="rounded-lg bg-orange-500 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-orange-600"
        >
          {topic.user_progress?.fire_completed ? 'Повторить FIRe-flow' : 'Начать FIRe-flow'}
        </Link>
        {problems.length > 0 && (
          <Link
            to={`/topics/${topic.id}/practice`}
            className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Решать задания
          </Link>
        )}
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
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">Теория</h2>
          <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            <MathRenderer content={topic.description} />
          </div>
        </section>
      )}

      {/* Prototypes section */}
      {prototypes.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">
            Прототипы <span className="text-sm font-normal text-gray-400 dark:text-gray-500">({prototypes.length})</span>
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {prototypes.map((proto) => (
              <div
                key={proto.id}
                className="rounded-xl border border-gray-200 bg-white p-4 transition-colors hover:border-blue-200 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-800"
              >
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-sm font-bold text-blue-600 dark:text-blue-400">{proto.prototype_code}</span>
                  <span className="font-medium text-gray-900 dark:text-gray-100">{proto.title}</span>
                </div>
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  {difficultyBadge(proto.difficulty_within_task)}
                  {proto.estimated_study_minutes && (
                    <span className="text-xs text-gray-400 dark:text-gray-500">~{proto.estimated_study_minutes} мин</span>
                  )}
                </div>
                {proto.description && (
                  <p className="mb-3 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{proto.description}</p>
                )}
                <div className="flex gap-2">
                  <Link
                    to={`/prototypes/${proto.id}`}
                    className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-blue-700"
                  >
                    Теория
                  </Link>
                  <Link
                    to={`/prototypes/${proto.id}`}
                    className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
                  >
                    Практика
                  </Link>
                </div>
              </div>
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

      {/* Problems section */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">
          Задания <span className="text-sm font-normal text-gray-400 dark:text-gray-500">({problems.length})</span>
        </h2>
        {problems.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Задания по этой теме пока не добавлены.</p>
        ) : (
          <div className="space-y-3">
            {problems.map((problem, idx) => (
              <div
                key={problem.id}
                className="rounded-lg border border-gray-200 bg-white p-4 transition-colors hover:border-blue-200 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-800"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Задание {idx + 1}</span>
                      {difficultyBadge(problem.difficulty)}
                      {problem.source && (
                        <span className="text-xs text-gray-400 dark:text-gray-500">{problem.source}</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <ProblemContent
                        text={problem.problem_text.slice(0, 200) + (problem.problem_text.length > 200 ? '...' : '')}
                        images={problem.problem_images}
                        imageClassName="h-auto max-h-24 rounded bg-white p-1 dark:invert"
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
