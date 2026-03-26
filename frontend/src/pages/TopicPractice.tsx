import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import ProblemCard from '../components/ProblemCard'
import { useFormulaStore } from '../stores/formulaStore'

interface Problem {
  id: string
  topic_id: string
  task_number: number
  difficulty: string
  problem_text: string
  problem_images?: string[] | null
  hints?: string[] | null
  source?: string | null
  max_points?: number | null
  prototype_id?: string | null
  prototype_code?: string | null
  prototype_title?: string | null
}

interface ProblemListResponse {
  items: Problem[]
  total: number
  page: number
  page_size: number
}

interface TopicInfo {
  id: string
  task_number: number
  title: string
}

export default function TopicPractice() {
  const { id } = useParams<{ id: string }>()
  const [topic, setTopic] = useState<TopicInfo | null>(null)
  const [problems, setProblems] = useState<Problem[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [completed, setCompleted] = useState(0)
  const [correctCount, setCorrectCount] = useState(0)
  const [totalXp, setTotalXp] = useState(0)
  const [finished, setFinished] = useState(false)
  const setActiveTask = useFormulaStore((s) => s.setActiveTask)

  // Set active task for formula sheet context
  useEffect(() => {
    if (topic) setActiveTask(topic.task_number)
    return () => setActiveTask(null)
  }, [topic, setActiveTask])

  useEffect(() => {
    if (!id) return

    setLoading(true)
    setError(null)

    Promise.all([
      api<TopicInfo>(`/api/topics/${id}`),
      api<ProblemListResponse>(`/api/problems?topic_id=${id}&page_size=50`),
    ])
      .then(([topicData, problemsData]) => {
        setTopic(topicData)
        setProblems(problemsData.items)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  const currentProblem = problems[currentIndex] ?? null

  const handleComplete = useCallback((_assessment: string, result: { is_correct: boolean; xp_earned: number }) => {
    setCompleted((c) => c + 1)
    if (result.is_correct) setCorrectCount((c) => c + 1)
    setTotalXp((x) => x + result.xp_earned)

    setTimeout(() => {
      setCurrentIndex((i) => {
        if (i < problems.length - 1) return i + 1
        setFinished(true)
        return i
      })
    }, 1000)
  }, [problems.length])

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-4 h-8 w-64 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-64 animate-pulse rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
      </div>
    )
  }

  if (error || !topic) {
    return (
      <div className="p-8">
        <Link to={`/topics/${id}`} className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline">
          &larr; Назад к теме
        </Link>
        <p className="mt-4 text-red-600">Ошибка загрузки: {error || 'Тема не найдена'}</p>
      </div>
    )
  }

  if (problems.length === 0) {
    return (
      <div className="p-8">
        <Link to={`/topics/${id}`} className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline">
          &larr; Назад к теме
        </Link>
        <div className="mt-8 text-center">
          <p className="text-lg text-gray-500 dark:text-gray-400">Задания по этой теме пока не добавлены.</p>
        </div>
      </div>
    )
  }

  if (finished) {
    const accuracy = completed > 0 ? Math.round((correctCount / completed) * 100) : 0
    return (
      <div className="p-8">
        <div className="mx-auto max-w-lg text-center">
          <div className="mb-6 text-5xl">🎉</div>
          <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-gray-100">Все задания решены!</h1>
          <p className="mb-8 text-gray-500 dark:text-gray-400">Тема: {topic.title}</p>

          <div className="mb-8 grid grid-cols-3 gap-4">
            <div className="rounded-lg border border-gray-200 bg-white p-4 text-center dark:border-gray-700 dark:bg-gray-800">
              <div className="text-2xl font-bold text-blue-600">{completed}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Решено</div>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4 text-center dark:border-gray-700 dark:bg-gray-800">
              <div className="text-2xl font-bold text-green-600">{accuracy}%</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Точность</div>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4 text-center dark:border-gray-700 dark:bg-gray-800">
              <div className="text-2xl font-bold text-purple-600">+{totalXp}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">XP</div>
            </div>
          </div>

          <div className="flex justify-center gap-3">
            <Link
              to={`/topics/${id}`}
              className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              К теме
            </Link>
            <Link
              to="/topics"
              className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              Все темы
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <Link to={`/topics/${id}`} className="inline-flex items-center text-sm text-blue-600 hover:underline">
          &larr; Назад к теме
        </Link>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {topic.title}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="mb-1.5 flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            Задание {currentIndex + 1} из {problems.length}
          </span>
          <span className="text-gray-400 dark:text-gray-500">
            {completed} решено {totalXp > 0 && `\u2022 +${totalXp} XP`}
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-300"
            style={{ width: `${(completed / problems.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Current problem */}
      {currentProblem && (
        <ProblemCard
          key={currentProblem.id}
          problem={currentProblem}
          onComplete={handleComplete}
          showTimer
        />
      )}
    </div>
  )
}
