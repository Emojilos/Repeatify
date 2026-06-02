import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import MathRenderer from '../components/MathRenderer'
import ProblemContent from '../components/ProblemContent'
import { useAuthStore } from '../stores/authStore'
import { useFormulaStore } from '../stores/formulaStore'

interface Problem {
  id: string
  topic_id: string
  task_number: number
  difficulty: string
  problem_text: string
  problem_images?: string[] | null
  solution_images?: string[] | null
  hints?: string[] | null
  max_points?: number | null
  category?: string | null
  subcategory?: string | null
  prototype_id?: string | null
  prototype_code?: string | null
  prototype_title?: string | null
}

interface AttemptResponse {
  is_correct: boolean
  correct_answer: string
  solution_markdown: string | null
  solution_images?: string[] | null
  xp_earned: number
  attempt_id: string
  new_level_reached: number | null
}

interface SolutionResponse {
  solution_markdown: string | null
  solution_images?: string[] | null
  correct_answer: string | null
}

function difficultyBadge(level: string) {
  const styles: Record<string, string> = {
    basic: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300',
    easy: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300',
    medium: 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300',
    hard: 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-300',
    olympiad: 'border-violet-200 bg-violet-50 text-violet-700 dark:border-violet-800 dark:bg-violet-950/40 dark:text-violet-300',
  }
  const labels: Record<string, string> = {
    basic: 'Базовый',
    easy: 'Базовый',
    medium: 'Средний',
    hard: 'Сложный',
    olympiad: 'Олимпиадный',
  }

  return (
    <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${styles[level] || 'border-gray-200 bg-white text-gray-600 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300'}`}>
      {labels[level] || level}
    </span>
  )
}

function hasSolutionPayload(solution: SolutionResponse | AttemptResponse | null) {
  return Boolean(
    solution?.correct_answer ||
    solution?.solution_markdown ||
    (solution?.solution_images && solution.solution_images.length > 0),
  )
}

export default function ProblemSolve() {
  const { id } = useParams<{ id: string }>()
  const loadUser = useAuthStore((s) => s.loadUser)
  const setActiveTask = useFormulaStore((s) => s.setActiveTask)

  const [problem, setProblem] = useState<Problem | null>(null)
  const [answer, setAnswer] = useState('')
  const [attempt, setAttempt] = useState<AttemptResponse | null>(null)
  const [solution, setSolution] = useState<SolutionResponse | null>(null)
  const [showAnswer, setShowAnswer] = useState(false)
  const [hintsShown, setHintsShown] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [solutionLoading, setSolutionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [startedAt, setStartedAt] = useState(() => Date.now())
  const inputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!id) return

    let cancelled = false

    async function loadProblem() {
      setLoading(true)
      setError(null)
      setAttempt(null)
      setSolution(null)
      setShowAnswer(false)
      setHintsShown(0)
      setStartedAt(Date.now())

      try {
        const data = await api<Problem>(`/api/problems/${id}`)
        if (!cancelled) setProblem(data)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Не удалось загрузить задание')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadProblem()

    return () => {
      cancelled = true
    }
  }, [id])

  useEffect(() => {
    if (problem?.task_number) setActiveTask(problem.task_number)
    return () => setActiveTask(null)
  }, [problem?.task_number, setActiveTask])

  const isPart2 = (problem?.task_number ?? 0) >= 13
  const displayedSolution = solution ?? (showAnswer && attempt ? attempt : null)

  async function fetchSolution() {
    if (!problem || solutionLoading) return null

    setSolutionLoading(true)
    setError(null)
    try {
      const data = await api<SolutionResponse>(`/api/problems/${problem.id}/solution`)
      setSolution(data)
      setShowAnswer(true)
      return data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить решение')
      return null
    } finally {
      setSolutionLoading(false)
    }
  }

  async function checkAnswer() {
    if (!problem || !answer.trim() || submitting) return

    setSubmitting(true)
    setError(null)
    setAttempt(null)
    setShowAnswer(false)
    setSolution(null)

    try {
      const data = await api<AttemptResponse>(`/api/problems/${problem.id}/attempt`, {
        method: 'POST',
        body: JSON.stringify({
          answer: answer.trim(),
          time_spent_seconds: Math.max(0, Math.round((Date.now() - startedAt) / 1000)),
          self_assessment: 'good',
        }),
      })

      setAttempt(data)
      loadUser()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось проверить ответ')
    } finally {
      setSubmitting(false)
    }
  }

  function tryAgain() {
    setAttempt(null)
    setSolution(null)
    setShowAnswer(false)
    setAnswer('')
    setStartedAt(Date.now())
    window.setTimeout(() => inputRef.current?.focus(), 0)
  }

  async function revealAnswer() {
    if (attempt) {
      setShowAnswer(true)
      if (!hasSolutionPayload(attempt)) await fetchSolution()
      return
    }
    await fetchSolution()
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl p-6 lg:p-10">
        <div className="mb-5 h-5 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-800" />
        <div className="h-[420px] animate-pulse rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900" />
      </div>
    )
  }

  if (error && !problem) {
    return (
      <div className="mx-auto max-w-3xl p-6 lg:p-10">
        <Link to="/topics" className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400">
          Все задания
        </Link>
        <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      </div>
    )
  }

  if (!problem) return null

  return (
    <div className="min-h-full bg-gray-50 dark:bg-gray-950">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-10 lg:py-10">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <Link to="/topics" className="font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
              Задания
            </Link>
            <span className="text-gray-300 dark:text-gray-700">/</span>
            <Link to={`/topics/${problem.topic_id}`} className="font-medium text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100">
              Задание {problem.task_number}
            </Link>
            {problem.subcategory && (
              <>
                <span className="text-gray-300 dark:text-gray-700">/</span>
                <span className="max-w-[42rem] truncate text-gray-500 dark:text-gray-400">{problem.subcategory}</span>
              </>
            )}
          </div>
          <Link
            to={`/topics/${problem.topic_id}`}
            className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition-colors hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-200 dark:hover:border-gray-700"
          >
            К списку задач
          </Link>
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <article className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <header className="border-b border-gray-100 px-5 py-5 dark:border-gray-800 sm:px-7">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <span className="rounded-xl bg-gray-950 px-3 py-1.5 text-sm font-semibold text-white dark:bg-white dark:text-gray-950">
                      Задание {problem.task_number}
                    </span>
                    {difficultyBadge(problem.difficulty)}
                    {problem.max_points && (
                      <span className="rounded-full border border-gray-200 bg-white px-2.5 py-1 text-xs font-medium text-gray-500 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400">
                        {problem.max_points} {problem.max_points === 1 ? 'балл' : 'балла'}
                      </span>
                    )}
                  </div>
                  <h1 className="text-xl font-semibold tracking-tight text-gray-950 dark:text-gray-50">
                    {problem.subcategory || problem.category || `Задание ${problem.task_number}`}
                  </h1>
                </div>
                {problem.prototype_id && (
                  <Link
                    to={`/prototypes/${problem.prototype_id}`}
                    className="rounded-lg border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    Теория
                  </Link>
                )}
              </div>
            </header>

            <div className="px-5 py-6 sm:px-7">
              <div className="prose prose-gray max-w-none text-lg leading-relaxed dark:prose-invert">
                <ProblemContent
                  text={problem.problem_text}
                  images={problem.problem_images}
                  imageClassName="h-auto max-h-[480px] rounded-xl border border-gray-200 bg-white p-2 dark:border-gray-800 dark:bg-gray-950 dark:invert-0"
                />
              </div>
            </div>

            {problem.hints && problem.hints.length > 0 && !showAnswer && !attempt?.is_correct && (
              <div className="border-t border-gray-100 px-5 py-4 dark:border-gray-800 sm:px-7">
                {hintsShown > 0 && (
                  <div className="mb-3 space-y-2">
                    {problem.hints.slice(0, hintsShown).map((hint, index) => (
                      <div
                        key={`${hint}-${index}`}
                        className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/70 dark:bg-amber-950/30 dark:text-amber-200"
                      >
                        <span className="mr-1 font-semibold">Подсказка {index + 1}.</span>
                        <MathRenderer content={hint} />
                      </div>
                    ))}
                  </div>
                )}
                {hintsShown < problem.hints.length && (
                  <button
                    type="button"
                    onClick={() => setHintsShown((value) => value + 1)}
                    className="rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm font-semibold text-amber-700 transition-colors hover:bg-amber-50 dark:border-amber-900/70 dark:bg-gray-900 dark:text-amber-300 dark:hover:bg-amber-950/30"
                  >
                    {hintsShown === 0 ? 'Показать подсказку' : 'Следующая подсказка'}
                  </button>
                )}
              </div>
            )}

            <section className="border-t border-gray-100 px-5 py-5 dark:border-gray-800 sm:px-7">
              {!isPart2 ? (
                <div className="space-y-4">
                  <label className="block">
                    <span className="mb-2 block text-sm font-semibold text-gray-800 dark:text-gray-200">Ответ</span>
                    <div className="flex flex-col gap-3 sm:flex-row">
                      <input
                        ref={inputRef}
                        type="text"
                        value={answer}
                        onChange={(event) => setAnswer(event.target.value)}
                        onKeyDown={(event) => event.key === 'Enter' && checkAnswer()}
                        disabled={submitting || Boolean(attempt?.is_correct)}
                        placeholder="Введите краткий ответ"
                        className="min-h-12 flex-1 rounded-xl border border-gray-200 bg-white px-4 text-base text-gray-950 outline-none transition focus:border-gray-950 focus:ring-4 focus:ring-gray-950/5 disabled:bg-gray-50 disabled:text-gray-500 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-50 dark:focus:border-gray-200 dark:focus:ring-white/10 dark:disabled:bg-gray-900"
                        autoFocus
                      />
                      <button
                        type="button"
                        onClick={checkAnswer}
                        disabled={!answer.trim() || submitting || Boolean(attempt?.is_correct)}
                        className="min-h-12 rounded-xl bg-gray-950 px-6 text-sm font-semibold text-white transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-200 dark:disabled:bg-gray-700 dark:disabled:text-gray-400"
                      >
                        {submitting ? 'Проверяю...' : 'Проверить'}
                      </button>
                    </div>
                  </label>

                  {attempt && (
                    <div
                      className={`rounded-2xl border px-4 py-4 ${
                        attempt.is_correct
                          ? 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/70 dark:bg-emerald-950/30 dark:text-emerald-200'
                          : 'border-red-200 bg-red-50 text-red-900 dark:border-red-900/70 dark:bg-red-950/30 dark:text-red-200'
                      }`}
                    >
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <div className="text-sm font-semibold">
                            {attempt.is_correct ? 'Ответ верный' : 'Ответ не совпал'}
                          </div>
                          <p className="mt-1 text-sm opacity-80">
                            {attempt.is_correct
                              ? 'Можно открыть решение и сверить ход рассуждения.'
                              : 'Можно попробовать ещё раз или сразу открыть ответ.'}
                          </p>
                        </div>
                        {attempt.is_correct ? (
                          <button
                            type="button"
                            onClick={revealAnswer}
                            className="rounded-lg border border-emerald-300 bg-white px-4 py-2 text-sm font-semibold text-emerald-800 transition hover:bg-emerald-100 dark:border-emerald-800 dark:bg-gray-950 dark:text-emerald-200 dark:hover:bg-emerald-950"
                          >
                            {showAnswer ? 'Ответ открыт' : 'Показать решение'}
                          </button>
                        ) : (
                          <div className="flex flex-col gap-2 sm:flex-row">
                            <button
                              type="button"
                              onClick={tryAgain}
                              className="rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-semibold text-red-800 transition hover:bg-red-100 dark:border-red-800 dark:bg-gray-950 dark:text-red-200 dark:hover:bg-red-950"
                            >
                              Попробовать ещё
                            </button>
                            <button
                              type="button"
                              onClick={revealAnswer}
                              className="rounded-lg bg-red-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-800 dark:bg-red-500 dark:hover:bg-red-400"
                            >
                              Показать ответ
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-4 dark:border-gray-800 dark:bg-gray-950">
                    <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">Вторая часть</div>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      Здесь нет автоматической проверки. Откройте ответ и подробное решение, когда будете готовы свериться.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={fetchSolution}
                    disabled={solutionLoading}
                    className="min-h-12 w-full rounded-xl bg-gray-950 px-6 text-sm font-semibold text-white transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-200 dark:disabled:bg-gray-700 dark:disabled:text-gray-400"
                  >
                    {solutionLoading ? 'Загружаю...' : showAnswer ? 'Решение открыто' : 'Показать ответ и решение'}
                  </button>
                </div>
              )}

              {error && problem && (
                <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/70 dark:bg-red-950/30 dark:text-red-300">
                  {error}
                </div>
              )}
            </section>

            {showAnswer && (
              <section className="border-t border-gray-100 px-5 py-5 dark:border-gray-800 sm:px-7">
                <h2 className="mb-4 text-base font-semibold text-gray-950 dark:text-gray-50">Ответ и решение</h2>
                {hasSolutionPayload(displayedSolution) ? (
                  <div className="space-y-5">
                    {displayedSolution?.correct_answer && (
                      <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-4 dark:border-gray-800 dark:bg-gray-950">
                        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Ответ</div>
                        <div className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                          <MathRenderer content={displayedSolution.correct_answer} />
                        </div>
                      </div>
                    )}
                    {(displayedSolution?.solution_markdown || (displayedSolution?.solution_images && displayedSolution.solution_images.length > 0)) && (
                      <div className="rounded-2xl border border-gray-200 bg-white px-4 py-4 dark:border-gray-800 dark:bg-gray-950">
                        <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Подробное решение</div>
                        <ProblemContent
                          text={displayedSolution.solution_markdown || ''}
                          images={displayedSolution.solution_images}
                          imageClassName="h-auto max-h-[520px] rounded-xl border border-gray-200 bg-white p-2 dark:border-gray-800 dark:bg-gray-900 dark:invert-0"
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-4 text-sm text-gray-500 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-400">
                    Для этого задания пока нет сохранённого решения.
                  </div>
                )}
              </section>
            )}
          </article>

          <aside className="space-y-4">
            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900">
              <div className="text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500">Навигация</div>
              <div className="mt-4 space-y-2">
                <Link
                  to={`/topics/${problem.topic_id}`}
                  className="block rounded-xl border border-gray-200 px-4 py-3 text-sm font-semibold text-gray-700 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-200 dark:hover:border-gray-700 dark:hover:bg-gray-800"
                >
                  Вернуться к подкатегории
                </Link>
                <Link
                  to={`/topics/${problem.topic_id}/practice${problem.subcategory ? `?subcategory=${encodeURIComponent(problem.subcategory)}` : ''}`}
                  className="block rounded-xl border border-gray-200 px-4 py-3 text-sm font-semibold text-gray-700 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-200 dark:hover:border-gray-700 dark:hover:bg-gray-800"
                >
                  Решать подборку
                </Link>
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900">
              <div className="text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500">Параметры</div>
              <dl className="mt-4 space-y-3 text-sm">
                <div>
                  <dt className="text-gray-400 dark:text-gray-500">Номер</dt>
                  <dd className="mt-0.5 font-semibold text-gray-900 dark:text-gray-100">Задание {problem.task_number}</dd>
                </div>
                {problem.subcategory && (
                  <div>
                    <dt className="text-gray-400 dark:text-gray-500">Подкатегория</dt>
                    <dd className="mt-0.5 font-semibold text-gray-900 dark:text-gray-100">{problem.subcategory}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-gray-400 dark:text-gray-500">Формат</dt>
                  <dd className="mt-0.5 font-semibold text-gray-900 dark:text-gray-100">
                    {isPart2 ? 'Решение с разбором' : 'Проверка ответа'}
                  </dd>
                </div>
              </dl>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
