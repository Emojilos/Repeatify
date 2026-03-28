import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import MathRenderer from './MathRenderer'
import ProblemContent from './ProblemContent'
import { useXpStore, levelName } from '../stores/xpStore'
import { useAuthStore } from '../stores/authStore'

interface Problem {
  id: string
  topic_id: string
  task_number: number
  difficulty: string
  problem_text: string
  problem_images?: string[] | null
  hints?: string[] | null
  source?: string | null
  prototype_id?: string | null
  prototype_code?: string | null
  prototype_title?: string | null
}

interface AttemptResponse {
  is_correct: boolean
  correct_answer: string
  solution_markdown: string | null
  xp_earned: number
  attempt_id: string
  new_level_reached: number | null
}

type SelfAssessment = 'very hard' | 'hard' | 'normal' | 'easy'

interface ProblemCardProps {
  problem: Problem
  onComplete?: (assessment: SelfAssessment, result: AttemptResponse) => void
  showTimer?: boolean
  onSubmitOverride?: (answer: string, timeSpent: number, assessment: SelfAssessment) => Promise<AttemptResponse | null>
}

const assessmentButtons: { value: SelfAssessment; label: string; color: string }[] = [
  { value: 'very hard', label: 'Очень сложно', color: 'bg-red-500 hover:bg-red-600' },
  { value: 'hard', label: 'Сложно', color: 'bg-orange-500 hover:bg-orange-600' },
  { value: 'normal', label: 'Нормально', color: 'bg-green-500 hover:bg-green-600' },
  { value: 'easy', label: 'Легко', color: 'bg-blue-500 hover:bg-blue-600' },
]

function difficultyBadge(level: string) {
  const styles: Record<string, string> = {
    basic: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
    hard: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    olympiad: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  }
  const labels: Record<string, string> = {
    basic: 'Базовый',
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

export default function ProblemCard({ problem, onComplete, showTimer = false, onSubmitOverride }: ProblemCardProps) {
  const isPart2 = problem.task_number >= 13
  const notifyXp = useXpStore((s) => s.notifyXp)
  const showLevelUp = useXpStore((s) => s.showLevelUp)
  const loadUser = useAuthStore((s) => s.loadUser)

  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<AttemptResponse | null>(null)
  const [showSolution, setShowSolution] = useState(false)
  const [solutionText, setSolutionText] = useState<string | null>(null)
  const [loadingSolution, setLoadingSolution] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedAssessment, setSelectedAssessment] = useState<SelfAssessment | null>(null)
  const [hintsShown, setHintsShown] = useState(0)

  // Timer
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [timerActive, setTimerActive] = useState(showTimer)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (timerActive && !result) {
      timerRef.current = setInterval(() => {
        setElapsedSeconds((s) => s + 1)
      }, 1000)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [timerActive, result])

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const submitAttempt = useCallback(async (assessment: SelfAssessment) => {
    setSubmitting(true)
    setError(null)
    try {
      const answerText = isPart2 ? 'self-check' : answer.trim()
      let res: AttemptResponse | null
      if (onSubmitOverride) {
        res = await onSubmitOverride(answerText, elapsedSeconds, assessment)
      } else {
        res = await api<AttemptResponse>(`/api/problems/${problem.id}/attempt`, {
          method: 'POST',
          body: JSON.stringify({
            answer: answerText,
            time_spent_seconds: elapsedSeconds,
            self_assessment: assessment,
          }),
        })
      }
      if (res) {
        setResult(res)
        if (timerRef.current) clearInterval(timerRef.current)
        if (res.xp_earned > 0) {
          notifyXp(res.xp_earned)
          loadUser()
        }
        if (res.new_level_reached) {
          showLevelUp(res.new_level_reached, levelName(res.new_level_reached))
        }
      }
      return res
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка отправки')
      return null
    } finally {
      setSubmitting(false)
    }
  }, [problem.id, isPart2, answer, elapsedSeconds, onSubmitOverride])

  // Part 1: Check answer first, then show SRS buttons
  const handleCheck = async () => {
    if (!answer.trim()) return
    const res = await submitAttempt('normal')
    if (res) {
      setSelectedAssessment(null)
    }
  }

  const [correctAnswer, setCorrectAnswer] = useState<string | null>(null)

  // Part 2: Fetch solution, then let user self-assess
  const handleShowSolution = async () => {
    setLoadingSolution(true)
    try {
      const res = await api<{ solution_markdown: string | null; correct_answer: string | null }>(`/api/problems/${problem.id}/solution`)
      setSolutionText(res.solution_markdown)
      setCorrectAnswer(res.correct_answer)
    } catch {
      // Fallback: still show assessment even without solution
    } finally {
      setLoadingSolution(false)
      setShowSolution(true)
    }
  }

  const handlePart2Assess = async (assessment: SelfAssessment) => {
    const res = await submitAttempt(assessment)
    if (res) {
      setSelectedAssessment(assessment)
    }
  }

  // Part 1: after seeing result, user picks SRS assessment for the next review
  const handleSrsAssessment = (assessment: SelfAssessment) => {
    setSelectedAssessment(assessment)
    if (result && onComplete) {
      onComplete(assessment, result)
    }
  }

  // Stable ref for onComplete to avoid infinite loops
  const onCompleteRef = useRef(onComplete)
  onCompleteRef.current = onComplete

  // Part 2: after picking assessment and submitting
  const part2Completed = useRef(false)
  useEffect(() => {
    if (isPart2 && selectedAssessment && result && !part2Completed.current) {
      part2Completed.current = true
      onCompleteRef.current?.(selectedAssessment, result)
    }
  }, [isPart2, selectedAssessment, result])

  const checked = result !== null

  return (
    <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
            {problem.task_number}
          </span>
          {difficultyBadge(problem.difficulty)}
          {problem.prototype_code && problem.prototype_id && (
            <Link
              to={`/prototypes/${problem.prototype_id}`}
              className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-700 transition-colors hover:bg-indigo-200 dark:bg-indigo-900/40 dark:text-indigo-300 dark:hover:bg-indigo-900/60"
              title={problem.prototype_title || undefined}
            >
              {problem.prototype_code}
            </Link>
          )}
          {problem.source && (
            <span className="text-xs text-gray-400 dark:text-gray-500">{problem.source}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {problem.prototype_id && (
            <Link
              to={`/prototypes/${problem.prototype_id}`}
              className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs text-gray-500 transition-colors hover:bg-gray-50 hover:text-blue-600 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-blue-400"
            >
              К теории
            </Link>
          )}
          {showTimer && (
            <button
              onClick={() => setTimerActive(!timerActive)}
              className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-700"
            >
              <span>{formatTime(elapsedSeconds)}</span>
              <span className="text-xs">{timerActive ? '\u23F8' : '\u25B6'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Problem text */}
      <div className="px-6 py-5">
        <ProblemContent text={problem.problem_text} images={problem.problem_images} />
      </div>

      {/* Progressive hints */}
      {problem.hints && problem.hints.length > 0 && !checked && (
        <div className="border-t border-gray-100 px-6 py-3 dark:border-gray-700">
          {hintsShown > 0 && (
            <div className="mb-3 space-y-2">
              {problem.hints.slice(0, hintsShown).map((hint, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                >
                  <span className="mr-1.5 font-medium">Подсказка {i + 1}:</span>
                  <MathRenderer content={hint} />
                </div>
              ))}
            </div>
          )}
          {hintsShown < problem.hints.length && (
            <button
              onClick={() => setHintsShown((h) => h + 1)}
              className="text-sm font-medium text-amber-600 hover:text-amber-700 dark:text-amber-400 dark:hover:text-amber-300"
            >
              {hintsShown === 0 ? 'Подсказка' : 'Ещё подсказка'} ({hintsShown}/{problem.hints.length})
            </button>
          )}
        </div>
      )}

      {/* Answer section */}
      <div className="border-t border-gray-100 px-6 py-4 dark:border-gray-700">
        {!isPart2 ? (
          /* Part 1: numeric answer input */
          <>
            {!checked ? (
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
                  placeholder="Введите ответ..."
                  className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
                  disabled={submitting}
                  autoFocus
                />
                <button
                  onClick={handleCheck}
                  disabled={!answer.trim() || submitting}
                  className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting ? 'Проверка...' : 'Проверить'}
                </button>
              </div>
            ) : (
              /* Result display */
              <div>
                <div className={`mb-4 flex items-center gap-3 rounded-lg p-3 ${result.is_correct ? 'bg-green-50 dark:bg-green-900/30' : 'bg-red-50 dark:bg-red-900/30'}`}>
                  <span className={`text-2xl ${result.is_correct ? 'text-green-500' : 'text-red-500'}`}>
                    {result.is_correct ? '\u2713' : '\u2717'}
                  </span>
                  <div>
                    <div className={`font-semibold ${result.is_correct ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'}`}>
                      {result.is_correct ? 'Правильно!' : 'Неправильно'}
                    </div>
                    {!result.is_correct && (
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Правильный ответ: <span className="font-medium">{result.correct_answer}</span>
                      </div>
                    )}
                    {result.xp_earned > 0 && (
                      <div className="text-sm font-medium text-blue-600">+{result.xp_earned} XP</div>
                    )}
                  </div>
                </div>

                {/* Solution toggle */}
                {result.solution_markdown && (
                  <div className="mb-4">
                    <button
                      onClick={() => setShowSolution(!showSolution)}
                      className="mb-2 text-sm font-medium text-blue-600 hover:underline"
                    >
                      {showSolution ? 'Скрыть решение' : 'Показать решение'}
                    </button>
                    {showSolution && (
                      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900">
                        <MathRenderer content={result.solution_markdown} />
                      </div>
                    )}
                  </div>
                )}

                {/* SRS assessment buttons */}
                {!selectedAssessment && (
                  <div>
                    <div className="mb-2 text-sm text-gray-500 dark:text-gray-400">Оцените сложность:</div>
                    <div className="flex gap-2">
                      {assessmentButtons.map((btn) => (
                        <button
                          key={btn.value}
                          onClick={() => handleSrsAssessment(btn.value)}
                          className={`flex-1 rounded-lg px-4 py-2 text-sm font-semibold text-white transition-colors ${btn.color}`}
                        >
                          {btn.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {selectedAssessment && (
                  <div className="text-sm text-gray-400 dark:text-gray-500">
                    Оценка: {assessmentButtons.find((b) => b.value === selectedAssessment)?.label}
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          /* Part 2: show solution + self-assessment */
          <>
            {!showSolution && !checked ? (
              <button
                onClick={handleShowSolution}
                disabled={loadingSolution}
                className="w-full rounded-lg bg-purple-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-purple-700 disabled:opacity-50"
              >
                {loadingSolution ? 'Загрузка...' : 'Показать решение'}
              </button>
            ) : !checked ? (
              /* Solution revealed, awaiting self-assessment */
              <div>
                <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900">
                  {solutionText ? (
                    <>
                      <div className="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Решение:</div>
                      <MathRenderer content={solutionText} />
                    </>
                  ) : correctAnswer ? (
                    <>
                      <div className="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Ответ:</div>
                      <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        <MathRenderer content={correctAnswer} />
                      </div>
                    </>
                  ) : (
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      Решение пока не добавлено. Оцените себя самостоятельно.
                    </div>
                  )}
                </div>
                <div className="mb-2 text-sm text-gray-500 dark:text-gray-400">Оцените, как вы справились:</div>
                <div className="flex gap-2">
                  {assessmentButtons.map((btn) => (
                    <button
                      key={btn.value}
                      onClick={() => handlePart2Assess(btn.value)}
                      disabled={submitting}
                      className={`flex-1 rounded-lg px-4 py-2 text-sm font-semibold text-white transition-colors ${btn.color} disabled:opacity-50`}
                    >
                      {btn.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* Part 2 result */
              <div>
                {(result.solution_markdown || correctAnswer) && (
                  <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900">
                    {result.solution_markdown ? (
                      <>
                        <div className="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Решение:</div>
                        <MathRenderer content={result.solution_markdown} />
                      </>
                    ) : correctAnswer ? (
                      <>
                        <div className="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">Ответ:</div>
                        <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                          <MathRenderer content={correctAnswer} />
                        </div>
                      </>
                    ) : null}
                  </div>
                )}
                {result.xp_earned > 0 && (
                  <div className="mb-4 text-sm font-medium text-blue-600">+{result.xp_earned} XP</div>
                )}
                {selectedAssessment && (
                  <div className="text-sm text-gray-400 dark:text-gray-500">
                    Оценка: {assessmentButtons.find((b) => b.value === selectedAssessment)?.label}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="border-t border-red-100 bg-red-50 px-6 py-3 text-sm text-red-600 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400">
          {error}
        </div>
      )}
    </div>
  )
}
