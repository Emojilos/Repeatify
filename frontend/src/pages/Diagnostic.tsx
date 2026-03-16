import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import MathRenderer from '../components/MathRenderer'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface DiagnosticProblem {
  problem_id: string
  task_number: number
  problem_text: string
  problem_images?: string[] | null
}

interface DiagnosticStartResponse {
  problems: DiagnosticProblem[]
  total: number
}

interface DiagnosticResultItem {
  task_number: number
  is_correct: boolean | null
  self_assessment: string | null
  time_spent_seconds: number
}

interface DiagnosticResultResponse {
  results: DiagnosticResultItem[]
  total_correct: number
  total_answered: number
}

interface AnswerEntry {
  task_number: number
  answer: string | null
  self_assessment: string | null
  time_spent_seconds: number
}

/* ------------------------------------------------------------------ */
/*  Self-assessment labels for Part 2                                  */
/* ------------------------------------------------------------------ */

const SELF_ASSESSMENT_OPTIONS: {
  value: string
  label: string
  color: string
}[] = [
  {
    value: 'level_0',
    label: 'Не знаю как подступиться',
    color: 'border-red-400 bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300 dark:border-red-600',
  },
  {
    value: 'level_1',
    label: 'Начал, но не довёл',
    color: 'border-orange-400 bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-600',
  },
  {
    value: 'level_2',
    label: 'Решил, не уверен',
    color: 'border-yellow-400 bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 dark:border-yellow-600',
  },
  {
    value: 'level_3',
    label: 'Решил уверенно',
    color: 'border-green-400 bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300 dark:border-green-600',
  },
]

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function Diagnostic() {
  const navigate = useNavigate()

  /* ---- state ---- */
  const [problems, setProblems] = useState<DiagnosticProblem[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<AnswerEntry[]>([])

  const [inputValue, setInputValue] = useState('')
  const [selectedAssessment, setSelectedAssessment] = useState<string | null>(null)

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [results, setResults] = useState<DiagnosticResultResponse | null>(null)

  /* timer per problem */
  const timerRef = useRef(0)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const [elapsed, setElapsed] = useState(0)

  /* ---- timer helpers ---- */
  const startTimer = useCallback(() => {
    timerRef.current = 0
    setElapsed(0)
    intervalRef.current = setInterval(() => {
      timerRef.current += 1
      setElapsed((e) => e + 1)
    }, 1000)
  }, [])

  const stopTimer = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  /* ---- load problems ---- */
  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await api<DiagnosticStartResponse>(
          '/api/diagnostic/start',
          { method: 'POST' },
        )
        if (cancelled) return
        // Sort by task_number
        const sorted = [...data.problems].sort(
          (a, b) => a.task_number - b.task_number,
        )
        setProblems(sorted)
        setAnswers(
          sorted.map((p) => ({
            task_number: p.task_number,
            answer: null,
            self_assessment: null,
            time_spent_seconds: 0,
          })),
        )
        startTimer()
      } catch {
        if (cancelled) return
        setError('Не удалось загрузить диагностический тест.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
      stopTimer()
    }
  }, [startTimer, stopTimer])

  /* ---- derived ---- */
  const problem = problems[currentIndex]
  const isPart2 = problem ? problem.task_number >= 13 : false
  const total = problems.length
  const progressPercent = total > 0 ? ((currentIndex) / total) * 100 : 0

  const canAdvance = isPart2 ? selectedAssessment !== null : inputValue.trim() !== ''

  /* ---- format time ---- */
  function formatTime(s: number) {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  /* recommended time hint */
  function recommendedTime(taskNumber: number) {
    if (taskNumber <= 12) return '3-5 мин'
    if (taskNumber <= 17) return '10-15 мин'
    return '15-20 мин'
  }

  /* ---- save current answer and go next ---- */
  function handleNext() {
    stopTimer()
    const updated = [...answers]
    updated[currentIndex] = {
      ...updated[currentIndex],
      answer: isPart2 ? null : inputValue.trim() || null,
      self_assessment: isPart2 ? selectedAssessment : null,
      time_spent_seconds: timerRef.current,
    }
    setAnswers(updated)

    if (currentIndex < total - 1) {
      setCurrentIndex(currentIndex + 1)
      setInputValue('')
      setSelectedAssessment(null)
      startTimer()
    } else {
      handleSubmit(updated)
    }
  }

  /* ---- go back ---- */
  function handleBack() {
    if (currentIndex === 0) return
    stopTimer()
    // save current partial answer
    const updated = [...answers]
    updated[currentIndex] = {
      ...updated[currentIndex],
      answer: isPart2 ? null : inputValue.trim() || null,
      self_assessment: isPart2 ? selectedAssessment : null,
      time_spent_seconds: timerRef.current,
    }
    setAnswers(updated)

    const prevIdx = currentIndex - 1
    setCurrentIndex(prevIdx)
    // restore previous answer
    const prev = updated[prevIdx]
    const prevProblem = problems[prevIdx]
    if (prevProblem.task_number >= 13) {
      setSelectedAssessment(prev.self_assessment)
      setInputValue('')
    } else {
      setInputValue(prev.answer || '')
      setSelectedAssessment(null)
    }
    startTimer()
  }

  /* ---- submit all answers ---- */
  async function handleSubmit(finalAnswers: AnswerEntry[]) {
    setSubmitting(true)
    setError(null)
    try {
      const data = await api<DiagnosticResultResponse>(
        '/api/diagnostic/submit',
        {
          method: 'POST',
          body: JSON.stringify({ answers: finalAnswers }),
        },
      )
      setResults(data)
    } catch {
      setError('Не удалось отправить результаты. Попробуйте ещё раз.')
      // re-enable so user can retry
      setSubmitting(false)
    }
  }

  /* ---- loading state ---- */
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            Загрузка диагностики...
          </p>
        </div>
      </div>
    )
  }

  /* ---- error state (no problems loaded) ---- */
  if (error && problems.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 max-w-md text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-5 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            На главную
          </button>
        </div>
      </div>
    )
  }

  /* ---- results screen ---- */
  if (results) {
    const part1Results = results.results.filter((r) => r.task_number <= 12)
    const part2Results = results.results.filter((r) => r.task_number >= 13)
    const part1Correct = part1Results.filter((r) => r.is_correct).length
    const totalTime = results.results.reduce(
      (sum, r) => sum + r.time_spent_seconds,
      0,
    )

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Диагностика завершена
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Время: {formatTime(totalTime)}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 sm:p-8 mb-6">
            {/* Summary */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {results.total_correct}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Правильно (Ч1)
                </div>
              </div>
              <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-xl">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {part1Correct}/{part1Results.length}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Часть 1
                </div>
              </div>
              <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {part2Results.length}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Часть 2
                </div>
              </div>
            </div>

            {/* Part 1 results */}
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
              Часть 1 (задания 1-12)
            </h3>
            <div className="grid grid-cols-4 sm:grid-cols-6 gap-2 mb-6">
              {part1Results.map((r) => (
                <div
                  key={r.task_number}
                  className={`p-2 rounded-lg text-center text-sm font-medium ${
                    r.is_correct
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                  }`}
                >
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    #{r.task_number}
                  </div>
                  {r.is_correct ? 'OK' : 'X'}
                </div>
              ))}
            </div>

            {/* Part 2 results */}
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
              Часть 2 (задания 13-19)
            </h3>
            <div className="space-y-2 mb-6">
              {part2Results.map((r) => {
                const opt = SELF_ASSESSMENT_OPTIONS.find(
                  (o) => o.value === r.self_assessment,
                )
                return (
                  <div
                    key={r.task_number}
                    className="flex items-center justify-between p-2 rounded-lg bg-gray-50 dark:bg-gray-700/50"
                  >
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Задание {r.task_number}
                    </span>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {opt?.label || r.self_assessment || '—'}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex justify-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
            >
              Перейти к плану
            </button>
          </div>
        </div>
      </div>
    )
  }

  /* ---- main test UI ---- */
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex flex-col">
      {/* Top bar: progress */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Задание {currentIndex + 1} из {total}
            </span>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {formatTime(elapsed)}
              </span>
              <span className="text-xs text-gray-400 dark:text-gray-500">
                (~{recommendedTime(problem.task_number)})
              </span>
            </div>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Problem card */}
      <div className="flex-1 flex items-start justify-center p-4 pt-6 sm:pt-10">
        <div className="w-full max-w-3xl">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 sm:p-8">
            {/* Task number badge */}
            <div className="flex items-center gap-2 mb-4">
              <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm font-semibold">
                Задание {problem.task_number}
              </span>
              {isPart2 && (
                <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-xs">
                  Часть 2
                </span>
              )}
            </div>

            {/* Problem text */}
            <div className="mb-6">
              <MathRenderer content={problem.problem_text} />
            </div>

            {/* Answer area */}
            {!isPart2 ? (
              /* Part 1: number input */
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Ваш ответ:
                </label>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && canAdvance) handleNext()
                  }}
                  placeholder="Введите ответ..."
                  autoFocus
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white bg-white dark:bg-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-lg"
                />
              </div>
            ) : (
              /* Part 2: self-assessment */
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Оцените свой уровень по этому заданию:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {SELF_ASSESSMENT_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setSelectedAssessment(opt.value)}
                      className={`p-3 rounded-xl border-2 text-left text-sm font-medium transition-all ${
                        selectedAssessment === opt.value
                          ? opt.color + ' ring-2 ring-offset-1 ring-blue-400'
                          : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-500'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <p className="text-red-600 dark:text-red-400 text-sm mt-4">
                {error}
              </p>
            )}

            {/* Navigation */}
            <div className="flex justify-between mt-8">
              <button
                onClick={handleBack}
                disabled={currentIndex === 0}
                className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  currentIndex === 0
                    ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                Назад
              </button>
              <button
                onClick={handleNext}
                disabled={!canAdvance || submitting}
                className="px-6 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {submitting
                  ? 'Отправка...'
                  : currentIndex === total - 1
                    ? 'Завершить'
                    : 'Далее'}
              </button>
            </div>
          </div>

          {/* Quick navigation dots */}
          <div className="flex flex-wrap justify-center gap-1.5 mt-4">
            {problems.map((p, i) => {
              const a = answers[i]
              const answered = a?.answer !== null || a?.self_assessment !== null
              return (
                <div
                  key={p.task_number}
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium ${
                    i === currentIndex
                      ? 'bg-blue-600 text-white'
                      : answered
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {p.task_number}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
