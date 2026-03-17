import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import MathRenderer from '../components/MathRenderer'
import YouTubePlayer from '../components/YouTubePlayer'

interface PrototypeResponse {
  id: string
  task_number: number
  prototype_code: string
  title: string
  description: string | null
  difficulty_within_task: string
  estimated_study_minutes: number | null
  theory_markdown: string | null
  key_formulas: { name: string; formula: string; description?: string }[] | null
  solution_algorithm: { step: number; title: string; description: string }[] | null
  common_mistakes: { title: string; description: string; correct?: string }[] | null
  related_prototypes: { id: string; prototype_code: string; title: string }[] | null
  order_index: number | null
}

interface VideoResource {
  id: string
  prototype_id: string
  youtube_video_id: string
  title: string
  channel_name: string | null
  duration_seconds: number | null
  timestamps: { time: number; label: string }[] | null
  order_index: number | null
}

interface Problem {
  id: string
  topic_id: string
  task_number: number
  difficulty: string
  problem_text: string
  source: string | null
  max_points: number | null
}

interface ProblemListResponse {
  items: Problem[]
  total: number
  page: number
  page_size: number
}

const difficultyStyles: Record<string, string> = {
  easy: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  hard: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
}

const difficultyLabels: Record<string, string> = {
  easy: 'Легко',
  medium: 'Средне',
  hard: 'Сложно',
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s > 0 ? `${m}:${s.toString().padStart(2, '0')}` : `${m} мин`
}

export default function PrototypeDetail() {
  const { id } = useParams<{ id: string }>()
  const [prototype, setPrototype] = useState<PrototypeResponse | null>(null)
  const [videos, setVideos] = useState<VideoResource[]>([])
  const [problems, setProblems] = useState<Problem[]>([])
  const [problemsTotal, setProblemsTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return

    setLoading(true)
    setError(null)

    Promise.all([
      api<PrototypeResponse>(`/api/prototypes/${id}`),
      api<VideoResource[]>(`/api/prototypes/${id}/videos`),
      api<ProblemListResponse>(`/api/prototypes/${id}/problems?page_size=10`),
    ])
      .then(([protoData, videosData, problemsData]) => {
        setPrototype(protoData)
        setVideos(videosData)
        setProblems(problemsData.items)
        setProblemsTotal(problemsData.total)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl p-8">
        <div className="mb-4 h-5 w-32 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="mb-2 h-8 w-80 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="mb-6 h-4 w-64 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="mb-8 h-64 animate-pulse rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !prototype) {
    return (
      <div className="mx-auto max-w-4xl p-8">
        <Link to="/topics" className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline dark:text-blue-400">
          &larr; Все темы
        </Link>
        <p className="mt-4 text-red-600">Ошибка загрузки: {error || 'Прототип не найден'}</p>
      </div>
    )
  }

  const diff = prototype.difficulty_within_task

  return (
    <div className="mx-auto max-w-4xl p-8">
      {/* Back link */}
      <Link to="/topics" className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline dark:text-blue-400">
        &larr; Все темы
      </Link>

      {/* Header */}
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-lg font-bold text-white">
            {prototype.task_number}
          </span>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {prototype.prototype_code}. {prototype.title}
            </h1>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${difficultyStyles[diff] || 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}`}>
            {difficultyLabels[diff] || diff}
          </span>
          {prototype.estimated_study_minutes && (
            <span className="text-gray-400 dark:text-gray-500">~{prototype.estimated_study_minutes} мин. на изучение</span>
          )}
          {prototype.description && (
            <span className="text-gray-500 dark:text-gray-400">{prototype.description}</span>
          )}
        </div>
      </div>

      {/* Theory markdown */}
      {prototype.theory_markdown && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">Теория</h2>
          <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            <MathRenderer content={prototype.theory_markdown} />
          </div>
        </section>
      )}

      {/* Key formulas */}
      {prototype.key_formulas && prototype.key_formulas.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">Ключевые формулы</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {prototype.key_formulas.map((f, i) => (
              <div
                key={i}
                className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20"
              >
                <div className="mb-1 text-sm font-medium text-blue-800 dark:text-blue-300">{f.name}</div>
                <div className="text-blue-900 dark:text-blue-100">
                  <MathRenderer content={f.formula} />
                </div>
                {f.description && (
                  <div className="mt-1 text-xs text-blue-600 dark:text-blue-400">{f.description}</div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Solution algorithm */}
      {prototype.solution_algorithm && prototype.solution_algorithm.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">Алгоритм решения</h2>
          <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
            <ol className="divide-y divide-gray-100 dark:divide-gray-700">
              {prototype.solution_algorithm.map((step) => (
                <li key={step.step} className="flex gap-4 p-4">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                    {step.step}
                  </span>
                  <div className="min-w-0">
                    <div className="font-medium text-gray-900 dark:text-gray-100">{step.title}</div>
                    <div className="mt-0.5 text-sm text-gray-600 dark:text-gray-400">
                      <MathRenderer content={step.description} />
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>
      )}

      {/* Common mistakes */}
      {prototype.common_mistakes && prototype.common_mistakes.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">Типичные ошибки</h2>
          <div className="space-y-3">
            {prototype.common_mistakes.map((mistake, i) => (
              <div
                key={i}
                className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
              >
                <div className="mb-1 font-medium text-red-800 dark:text-red-300">{mistake.title}</div>
                <div className="text-sm text-red-700 dark:text-red-400">
                  <MathRenderer content={mistake.description} />
                </div>
                {mistake.correct && (
                  <div className="mt-2 rounded border border-green-200 bg-green-50 p-2 text-sm text-green-800 dark:border-green-800 dark:bg-green-900/20 dark:text-green-300">
                    <span className="font-medium">Правильно: </span>
                    <MathRenderer content={mistake.correct} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* YouTube videos */}
      {videos.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">Видео</h2>
          <div className="space-y-6">
            {videos.map((video) => (
              <div
                key={video.id}
                className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
              >
                <div className="mb-3 flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-gray-100">{video.title}</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                      {video.channel_name && <span>{video.channel_name}</span>}
                      {video.duration_seconds && (
                        <>
                          {video.channel_name && <span>·</span>}
                          <span>{formatDuration(video.duration_seconds)}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <YouTubePlayer
                  videoId={video.youtube_video_id}
                  timestamps={video.timestamps || undefined}
                />
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Related prototypes */}
      {prototype.related_prototypes && prototype.related_prototypes.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200">Связанные прототипы</h2>
          <div className="flex flex-wrap gap-2">
            {prototype.related_prototypes.map((rel) => (
              <Link
                key={rel.id}
                to={`/prototypes/${rel.id}`}
                className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm transition-colors hover:border-blue-300 hover:bg-blue-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-700 dark:hover:bg-blue-900/30"
              >
                <span className="mr-1.5 font-semibold text-blue-600 dark:text-blue-400">{rel.prototype_code}</span>
                <span className="text-gray-700 dark:text-gray-300">{rel.title}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Problems / Practice */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
            Задачи <span className="text-sm font-normal text-gray-400 dark:text-gray-500">({problemsTotal})</span>
          </h2>
          {problemsTotal > 0 && (
            <Link
              to={`/topics/${problems[0]?.topic_id}/practice`}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              Практика
            </Link>
          )}
        </div>
        {problems.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Задачи для этого прототипа пока не добавлены.</p>
        ) : (
          <div className="space-y-3">
            {problems.map((problem, idx) => (
              <div
                key={problem.id}
                className="rounded-lg border border-gray-200 bg-white p-4 transition-colors hover:border-blue-200 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-800"
              >
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Задача {idx + 1}</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${difficultyStyles[problem.difficulty] || 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}`}>
                    {difficultyLabels[problem.difficulty] || problem.difficulty}
                  </span>
                  {problem.source && (
                    <span className="text-xs text-gray-400 dark:text-gray-500">{problem.source}</span>
                  )}
                </div>
                <div className="line-clamp-2 text-sm text-gray-600 dark:text-gray-400">
                  <MathRenderer content={problem.problem_text.slice(0, 200) + (problem.problem_text.length > 200 ? '...' : '')} />
                </div>
              </div>
            ))}
            {problemsTotal > problems.length && (
              <p className="text-center text-sm text-gray-400 dark:text-gray-500">
                Показано {problems.length} из {problemsTotal} задач
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  )
}
