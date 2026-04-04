import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import ProblemContent from '../components/ProblemContent'
import MathRenderer from '../components/MathRenderer'

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

interface SolutionResponse {
  solution_markdown: string | null
  correct_answer: string | null
}

interface CheckedProblem {
  problemId: string
  userAnswer: string
  correctAnswer: string
  isCorrect: boolean
  solution: string | null
}

function seededShuffle<T>(arr: T[], seed: number): T[] {
  const shuffled = [...arr]
  let s = seed
  for (let i = shuffled.length - 1; i > 0; i--) {
    s = (s * 1664525 + 1013904223) & 0xffffffff
    const j = ((s >>> 0) % (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

export default function PrintProblems() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const paramTask = parseInt(searchParams.get('task') || '0', 10)
  const paramCount = parseInt(searchParams.get('count') || '0', 10)
  const paramSeed = parseInt(searchParams.get('seed') || '0', 10)

  const [problems, setProblems] = useState<Problem[]>([])
  const [totalAvailable, setTotalAvailable] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fetched, setFetched] = useState(false)

  const [formTask, setFormTask] = useState(paramTask || 1)
  const [formCount, setFormCount] = useState(paramCount || 10)

  // Answer checking
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [checked, setChecked] = useState<Record<string, CheckedProblem>>({})
  const [checking, setChecking] = useState(false)

  // Save variant
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  const handleGenerate = useCallback(() => {
    const seed = Math.floor(Math.random() * 1000000)
    navigate(`/print?task=${formTask}&count=${formCount}&seed=${seed}`)
  }, [formTask, formCount, navigate])

  useEffect(() => {
    if (!paramTask || !paramCount || !paramSeed) return

    setFormTask(paramTask)
    setFormCount(paramCount)
    setLoading(true)
    setError(null)
    setChecked({})
    setAnswers({})

    api<ProblemListResponse>(`/api/problems?task_number=${paramTask}&page_size=100`)
      .then((data) => {
        const shuffled = seededShuffle(data.items, paramSeed)
        setProblems(shuffled.slice(0, paramCount))
        setTotalAvailable(data.total)
        setFetched(true)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [paramTask, paramCount, paramSeed])

  function setAnswer(problemId: string, value: string) {
    setAnswers((prev) => ({ ...prev, [problemId]: value }))
    // Clear previous check for this problem
    setChecked((prev) => {
      const next = { ...prev }
      delete next[problemId]
      return next
    })
  }

  async function handleCheckAll() {
    setChecking(true)
    const results: Record<string, CheckedProblem> = {}

    await Promise.all(
      problems.map(async (problem) => {
        const userAnswer = (answers[problem.id] || '').trim()
        if (!userAnswer) return

        try {
          const solution = await api<SolutionResponse>(`/api/problems/${problem.id}/solution`)
          const correct = (solution.correct_answer || '').trim()

          let isCorrect = false
          if (correct) {
            if (userAnswer.toLowerCase() === correct.toLowerCase()) {
              isCorrect = true
            } else {
              try {
                isCorrect = Math.abs(parseFloat(userAnswer) - parseFloat(correct)) < 0.001
              } catch { /* not numeric */ }
            }
          }

          results[problem.id] = {
            problemId: problem.id,
            userAnswer,
            correctAnswer: correct,
            isCorrect,
            solution: solution.solution_markdown,
          }
        } catch { /* skip on error */ }
      }),
    )

    setChecked(results)
    setChecking(false)
  }

  async function handleSave() {
    if (!saveName.trim() || !paramTask || !paramSeed) return
    setSaving(true)
    try {
      await api('/api/variants', {
        method: 'POST',
        body: JSON.stringify({
          name: saveName.trim(),
          task_number: paramTask,
          problem_count: paramCount,
          seed: paramSeed,
        }),
      })
      setSaveSuccess(true)
      setTimeout(() => {
        setShowSaveModal(false)
        setSaveSuccess(false)
        setSaveName('')
      }, 1500)
    } catch { /* toast handles it */ }
    finally { setSaving(false) }
  }

  const answeredCount = problems.filter((p) => (answers[p.id] || '').trim()).length
  const checkedCount = Object.keys(checked).length
  const correctCount = Object.values(checked).filter((c) => c.isCorrect).length

  return (
    <div>
      {/* Controls — hidden when printing */}
      <div className="print:hidden p-8">
        <Link to="/topics" className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline dark:text-blue-400">
          &larr; Все темы
        </Link>

        <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">Печать заданий</h1>

        <div className="mb-6 flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Номер задания
            </label>
            <select
              value={formTask}
              onChange={(e) => setFormTask(Number(e.target.value))}
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            >
              {Array.from({ length: 19 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>Задание {n}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Количество
            </label>
            <input
              type="number"
              min={1}
              max={100}
              value={formCount}
              onChange={(e) => setFormCount(Math.max(1, Math.min(100, Number(e.target.value))))}
              className="w-24 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>

          <button
            onClick={handleGenerate}
            className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Сгенерировать
          </button>

          {fetched && problems.length > 0 && (
            <>
              <button
                onClick={() => window.print()}
                className="rounded-lg border border-gray-300 bg-white px-5 py-2 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              >
                Распечатать
              </button>
              <button
                onClick={() => { setSaveName(`Задание ${paramTask} — ${paramCount} задач`); setShowSaveModal(true) }}
                className="rounded-lg border border-blue-300 bg-blue-50 px-5 py-2 text-sm font-semibold text-blue-700 transition-colors hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-900/50"
              >
                Сохранить
              </button>
              {answeredCount > 0 && (
                <button
                  onClick={handleCheckAll}
                  disabled={checking}
                  className="rounded-lg bg-green-600 px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-green-700 disabled:opacity-50"
                >
                  {checking ? 'Проверяю...' : 'Проверить ответы'}
                </button>
              )}
            </>
          )}
        </div>

        {/* Results summary */}
        {checkedCount > 0 && (
          <div className="mb-4 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Результат: <strong className="text-green-600">{correctCount}</strong> / {checkedCount} правильно
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className="h-full rounded-full bg-green-500 transition-all"
                  style={{ width: `${checkedCount > 0 ? (correctCount / checkedCount) * 100 : 0}%` }}
                />
              </div>
              <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
                {checkedCount > 0 ? Math.round((correctCount / checkedCount) * 100) : 0}%
              </span>
            </div>
          </div>
        )}

        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
            ))}
          </div>
        )}

        {error && <p className="text-red-600">{error}</p>}

        {fetched && !loading && (
          <p className="mb-4 text-sm text-gray-500 dark:text-gray-400">
            Показано {problems.length} из {totalAvailable} доступных заданий
          </p>
        )}
      </div>

      {/* Problems */}
      {fetched && problems.length > 0 && (
        <div className="print:p-0 px-8 pb-8">
          {/* Print header — visible only when printing */}
          <div className="hidden print:block mb-6">
            <h1 className="text-xl font-bold">Задание {formTask} — Вариант ({problems.length} задач)</h1>
            <div className="mt-1 text-sm text-gray-500">Repeatify</div>
          </div>

          <div className="space-y-6 print:space-y-4">
            {problems.map((problem, idx) => {
              const check = checked[problem.id]
              return (
                <div
                  key={problem.id}
                  className={`rounded-lg border bg-white p-5 dark:bg-gray-800 print:rounded-none print:border-0 print:border-b print:border-gray-300 print:p-4 print:bg-white ${
                    check
                      ? check.isCorrect
                        ? 'border-green-300 dark:border-green-700'
                        : 'border-red-300 dark:border-red-700'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                  style={{ pageBreakInside: 'avoid' }}
                >
                  <div className="mb-2 flex items-center gap-2">
                    <span className="text-sm font-bold text-gray-900 dark:text-gray-100 print:text-black">
                      {idx + 1}.
                    </span>
                    {check && (
                      <span className={`text-xs font-medium ${check.isCorrect ? 'text-green-600' : 'text-red-600'}`}>
                        {check.isCorrect ? 'Верно' : 'Неверно'}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-800 dark:text-gray-200 print:text-black">
                    <ProblemContent
                      text={problem.problem_text}
                      images={problem.problem_images}
                      imageClassName="h-auto max-h-48 rounded bg-white p-1 print:max-h-40"
                    />
                  </div>

                  {/* Answer input — hidden when printing */}
                  <div className="print:hidden mt-3">
                    <div className="flex items-center gap-2">
                      <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Ответ:</label>
                      <input
                        type="text"
                        value={answers[problem.id] || ''}
                        onChange={(e) => setAnswer(problem.id, e.target.value)}
                        placeholder="Введите ответ"
                        className={`w-48 rounded-lg border px-3 py-1.5 text-sm focus:outline-none focus:ring-1 dark:bg-gray-800 dark:text-gray-100 ${
                          check
                            ? check.isCorrect
                              ? 'border-green-400 bg-green-50 focus:ring-green-400 dark:border-green-700 dark:bg-green-900/20'
                              : 'border-red-400 bg-red-50 focus:ring-red-400 dark:border-red-700 dark:bg-red-900/20'
                            : 'border-gray-300 focus:ring-blue-400 dark:border-gray-600'
                        }`}
                      />
                      {check && !check.isCorrect && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          Правильный ответ: <strong className="text-green-600">{check.correctAnswer}</strong>
                        </span>
                      )}
                    </div>

                    {/* Solution explanation for wrong answers */}
                    {check && !check.isCorrect && check.solution && (
                      <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
                        <div className="mb-2 text-xs font-semibold text-red-700 dark:text-red-300">Разбор</div>
                        <div className="text-sm text-red-900 dark:text-red-100">
                          <MathRenderer content={check.solution} />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Save modal */}
      {showSaveModal && (
        <div className="print:hidden fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowSaveModal(false)}>
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl dark:bg-gray-800" onClick={(e) => e.stopPropagation()}>
            {saveSuccess ? (
              <div className="text-center">
                <div className="mb-2 text-3xl">&#10003;</div>
                <p className="text-sm font-medium text-green-600">Вариант сохранён!</p>
              </div>
            ) : (
              <>
                <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">Сохранить вариант</h3>
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder="Название варианта"
                  autoFocus
                  className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSave() }}
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowSaveModal(false)}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving || !saveName.trim()}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? 'Сохранение...' : 'Сохранить'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
