import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import MathRenderer from '../components/MathRenderer'

interface TaskMastery {
  task_number: number
  status: string // not_tested, weak, medium, good, mastered
  correct: number | null
  total: number | null
  assessed_at: string | null
}

interface PlanData {
  target_score: number
  tasks: TaskMastery[]
}

interface StudyPlanResponse {
  id: string
  user_id: string
  target_score: number
  plan_data: PlanData | null
  generated_at: string
  is_active: boolean
}

interface AssessmentProblem {
  id: string
  task_number: number
  difficulty: string | null
  problem_text: string
  problem_images?: string[] | null
  hints?: string[] | null
}

interface AssessmentDetail {
  problem_id: string
  is_correct: boolean
  correct_answer: string | null
  solution_markdown: string | null
}

interface AssessmentResult {
  task_number: number
  correct_count: number
  total_count: number
  status: string
  details: AssessmentDetail[]
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  not_tested: {
    label: 'Не проверено',
    color: 'text-gray-500 dark:text-gray-400',
    bg: 'bg-gray-100 dark:bg-gray-700',
    border: 'border-gray-200 dark:border-gray-700',
  },
  weak: {
    label: 'Слабо',
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
  },
  medium: {
    label: 'Средне',
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
  },
  good: {
    label: 'Хорошо',
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
  },
  mastered: {
    label: 'Освоено',
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
}

const TARGET_OPTIONS = [70, 80, 90, 100] as const

const POINTS: Record<number, number> = {
  1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
  7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1,
  13: 2, 14: 2, 15: 2, 16: 2, 17: 2, 18: 4, 19: 4,
}

export default function StudyPlan() {
  const [plan, setPlan] = useState<StudyPlanResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showTargetModal, setShowTargetModal] = useState(false)
  const [modalTarget, setModalTarget] = useState(80)
  const [saving, setSaving] = useState(false)

  // Assessment state
  const [assessmentTask, setAssessmentTask] = useState<number | null>(null)
  const [assessmentProblems, setAssessmentProblems] = useState<AssessmentProblem[]>([])
  const [currentProblemIndex, setCurrentProblemIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [assessmentLoading, setAssessmentLoading] = useState(false)
  const [assessmentResult, setAssessmentResult] = useState<AssessmentResult | null>(null)

  useEffect(() => {
    loadPlan()
  }, [])

  async function loadPlan() {
    setLoading(true)
    setError(null)
    try {
      const data = await api<StudyPlanResponse>('/api/study-plan/current', { silent: true })
      setPlan(data)
      setModalTarget(data.target_score)
    } catch (err: unknown) {
      const status = (err as { status?: number }).status
      if (status === 404) {
        setPlan(null)
      } else {
        setError((err as Error).message)
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveTarget() {
    setSaving(true)
    try {
      const endpoint = plan ? '/api/study-plan/recalculate' : '/api/study-plan/generate'
      const method = plan ? 'PUT' : 'POST'
      const data = await api<StudyPlanResponse>(endpoint, {
        method,
        body: JSON.stringify({ target_score: modalTarget }),
      })
      setPlan(data)
      setShowTargetModal(false)
    } catch (err: unknown) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const startAssessment = useCallback(async (taskNumber: number) => {
    setAssessmentLoading(true)
    setAssessmentResult(null)
    setCurrentProblemIndex(0)
    setAnswers({})
    setCurrentAnswer('')
    try {
      const data = await api<{ task_number: number; problems: AssessmentProblem[] }>(
        `/api/study-plan/assess/${taskNumber}`,
        { method: 'POST' },
      )
      setAssessmentTask(taskNumber)
      setAssessmentProblems(data.problems)
    } catch (err: unknown) {
      setError((err as Error).message)
    } finally {
      setAssessmentLoading(false)
    }
  }, [])

  function saveCurrentAnswer() {
    if (!assessmentProblems[currentProblemIndex]) return
    const problemId = assessmentProblems[currentProblemIndex].id
    setAnswers(prev => ({ ...prev, [problemId]: currentAnswer }))
  }

  function goToNextProblem() {
    saveCurrentAnswer()
    const nextIndex = currentProblemIndex + 1
    if (nextIndex < assessmentProblems.length) {
      setCurrentProblemIndex(nextIndex)
      const nextProblemId = assessmentProblems[nextIndex].id
      setCurrentAnswer(answers[nextProblemId] || '')
    }
  }

  function goToPrevProblem() {
    saveCurrentAnswer()
    if (currentProblemIndex > 0) {
      const prevIndex = currentProblemIndex - 1
      setCurrentProblemIndex(prevIndex)
      const prevProblemId = assessmentProblems[prevIndex].id
      setCurrentAnswer(answers[prevProblemId] || '')
    }
  }

  async function submitAssessment() {
    if (assessmentTask === null) return
    saveCurrentAnswer()

    // Build final answers with current answer included
    const currentProblem = assessmentProblems[currentProblemIndex]
    const finalAnswers = { ...answers }
    if (currentProblem) {
      finalAnswers[currentProblem.id] = currentAnswer
    }

    setAssessmentLoading(true)
    try {
      const answerList = assessmentProblems.map(p => ({
        problem_id: p.id,
        answer: finalAnswers[p.id] || '',
      }))

      const result = await api<AssessmentResult>(
        `/api/study-plan/assess/${assessmentTask}/submit`,
        {
          method: 'POST',
          body: JSON.stringify({ answers: answerList }),
        },
      )
      setAssessmentResult(result)
      // Reload plan to get updated mastery
      await loadPlan()
    } catch (err: unknown) {
      setError((err as Error).message)
    } finally {
      setAssessmentLoading(false)
    }
  }

  function closeAssessment() {
    setAssessmentTask(null)
    setAssessmentProblems([])
    setAssessmentResult(null)
    setCurrentProblemIndex(0)
    setAnswers({})
    setCurrentAnswer('')
  }

  // Loading skeleton
  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-6 h-10 w-48 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="mb-6 h-24 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-4 text-2xl font-bold dark:text-gray-100">Карта знаний</h1>
        <p className="text-red-600">{error}</p>
      </div>
    )
  }

  // No plan yet
  if (!plan) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-2xl font-bold dark:text-gray-100">Карта знаний</h1>
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-800">
          <h2 className="mb-2 text-lg font-semibold dark:text-gray-100">Выберите целевой балл</h2>
          <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
            Мы покажем, какие задания нужно освоить для достижения цели
          </p>
          <div className="mb-6 flex justify-center gap-3">
            {TARGET_OPTIONS.map(score => (
              <button
                key={score}
                onClick={() => setModalTarget(score)}
                className={`rounded-lg border px-5 py-3 text-lg font-semibold transition-colors ${
                  modalTarget === score
                    ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                    : 'border-gray-200 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                {score}
              </button>
            ))}
          </div>
          <button
            onClick={handleSaveTarget}
            disabled={saving}
            className="rounded-lg bg-blue-600 px-8 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Создаём...' : 'Начать'}
          </button>
        </div>
      </div>
    )
  }

  const pd = plan.plan_data
  if (!pd) return null

  const tasks = pd.tasks
  const masteredCount = tasks.filter(t => t.status === 'mastered').length
  const testedCount = tasks.filter(t => t.status !== 'not_tested').length
  const totalTasks = tasks.length
  const masteredPoints = tasks
    .filter(t => t.status === 'mastered')
    .reduce((sum, t) => sum + (POINTS[t.task_number] || 0), 0)
  const totalPoints = tasks.reduce((sum, t) => sum + (POINTS[t.task_number] || 0), 0)

  // Assessment in progress — show assessment UI
  if (assessmentTask !== null && assessmentProblems.length > 0 && !assessmentResult) {
    const problem = assessmentProblems[currentProblemIndex]
    return (
      <div className="p-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-xl font-bold dark:text-gray-100">
            Задание {assessmentTask} — Проверка знаний
          </h1>
          <button
            onClick={closeAssessment}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Отмена
          </button>
        </div>

        {/* Progress bar */}
        <div className="mb-6">
          <div className="mb-2 flex justify-between text-sm text-gray-500 dark:text-gray-400">
            <span>Вопрос {currentProblemIndex + 1} из {assessmentProblems.length}</span>
            <span>{Object.keys(answers).length} отвечено</span>
          </div>
          <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700">
            <div
              className="h-2 rounded-full bg-blue-500 transition-all"
              style={{ width: `${((currentProblemIndex + 1) / assessmentProblems.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Problem card */}
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
          {problem.difficulty && (
            <span className={`mb-3 inline-block rounded px-2 py-0.5 text-xs font-medium ${
              problem.difficulty === 'basic' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' :
              problem.difficulty === 'hard' ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' :
              'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300'
            }`}>
              {problem.difficulty === 'basic' ? 'Базовый' : problem.difficulty === 'hard' ? 'Сложный' : 'Средний'}
            </span>
          )}
          <div className="mb-4 text-gray-900 dark:text-gray-100">
            <MathRenderer content={problem.problem_text} />
          </div>
          {problem.problem_images && problem.problem_images.length > 0 && (
            <div className="mb-4 flex flex-wrap gap-2">
              {problem.problem_images.map((url, i) => (
                <img key={i} src={url} alt="" className="max-h-48 rounded-lg" />
              ))}
            </div>
          )}
          <div className="flex gap-3">
            <input
              type="text"
              value={currentAnswer}
              onChange={e => setCurrentAnswer(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  if (currentProblemIndex < assessmentProblems.length - 1) {
                    goToNextProblem()
                  }
                }
              }}
              placeholder="Ваш ответ..."
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              autoFocus
            />
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={goToPrevProblem}
            disabled={currentProblemIndex === 0}
            className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-30 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Назад
          </button>

          {currentProblemIndex < assessmentProblems.length - 1 ? (
            <button
              onClick={goToNextProblem}
              className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              Далее
            </button>
          ) : (
            <button
              onClick={submitAssessment}
              disabled={assessmentLoading}
              className="rounded-lg bg-green-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
            >
              {assessmentLoading ? 'Проверяем...' : 'Завершить тест'}
            </button>
          )}
        </div>
      </div>
    )
  }

  // Assessment result screen
  if (assessmentResult) {
    const cfg = STATUS_CONFIG[assessmentResult.status] || STATUS_CONFIG.not_tested
    return (
      <div className="p-8">
        <h1 className="mb-6 text-xl font-bold dark:text-gray-100">
          Результат — Задание {assessmentResult.task_number}
        </h1>

        <div className={`mb-6 rounded-xl border p-6 ${cfg.border} ${cfg.bg}`}>
          <div className="text-center">
            <p className={`text-4xl font-bold ${cfg.color}`}>
              {assessmentResult.correct_count}/{assessmentResult.total_count}
            </p>
            <p className={`mt-1 text-lg font-medium ${cfg.color}`}>{cfg.label}</p>
          </div>
        </div>

        {/* Per-problem breakdown */}
        <div className="mb-6 space-y-3">
          {assessmentResult.details.map((detail, i) => (
            <div
              key={detail.problem_id}
              className={`rounded-lg border p-4 ${
                detail.is_correct
                  ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
                  : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={`text-lg ${detail.is_correct ? 'text-green-600' : 'text-red-600'}`}>
                  {detail.is_correct ? '\u2713' : '\u2717'}
                </span>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Вопрос {i + 1}
                </span>
                {detail.correct_answer && !detail.is_correct && (
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    — Ответ: {detail.correct_answer}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            onClick={closeAssessment}
            className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            К карте знаний
          </button>
          <button
            onClick={() => {
              closeAssessment()
              if (assessmentResult) startAssessment(assessmentResult.task_number)
            }}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Пройти заново
          </button>
        </div>
      </div>
    )
  }

  // Main knowledge map view
  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold dark:text-gray-100">Карта знаний</h1>
        <button
          onClick={() => setShowTargetModal(true)}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          Цель: {pd.target_score}
        </button>
      </div>

      {/* Summary stats */}
      <div className="mb-6 grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Проверено</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{testedCount}/{totalTasks}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Освоено</p>
          <p className="text-2xl font-bold text-emerald-600">{masteredCount}/{totalTasks}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Баллы</p>
          <p className="text-2xl font-bold text-blue-600">{masteredPoints}/{totalPoints}</p>
        </div>
      </div>

      {/* Task cards grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tasks.map(task => {
          const cfg = STATUS_CONFIG[task.status] || STATUS_CONFIG.not_tested
          return (
            <div
              key={task.task_number}
              className={`rounded-xl border p-4 ${cfg.border} ${cfg.bg}`}
            >
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Задание {task.task_number}
                </h3>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.color} ${cfg.bg}`}>
                  {cfg.label}
                </span>
              </div>

              {/* Score bar */}
              {task.status !== 'not_tested' && task.correct !== null && task.total !== null ? (
                <div className="mb-3">
                  <div className="mb-1 flex justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>{task.correct}/{task.total} правильно</span>
                    <span>{Math.round((task.correct / task.total) * 100)}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-600">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        task.status === 'mastered' ? 'bg-emerald-500' :
                        task.status === 'good' ? 'bg-green-500' :
                        task.status === 'medium' ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${(task.correct / task.total) * 100}%` }}
                    />
                  </div>
                </div>
              ) : (
                <div className="mb-3">
                  <p className="text-xs text-gray-400 dark:text-gray-500">Ещё не проверено</p>
                </div>
              )}

              <button
                onClick={() => startAssessment(task.task_number)}
                disabled={assessmentLoading}
                className={`w-full rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                  task.status === 'not_tested'
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'border border-gray-300 text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                {task.status === 'not_tested' ? 'Проверить знания' : 'Пройти заново'}
              </button>
            </div>
          )
        })}
      </div>

      {/* Target score modal */}
      {showTargetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowTargetModal(false)}>
          <div
            className="mx-4 w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-800"
            onClick={e => e.stopPropagation()}
          >
            <h2 className="mb-5 text-lg font-bold dark:text-gray-100">Целевой балл</h2>
            <div className="mb-6 grid grid-cols-4 gap-2">
              {TARGET_OPTIONS.map(score => (
                <button
                  key={score}
                  onClick={() => setModalTarget(score)}
                  className={`rounded-lg border px-3 py-3 text-sm font-medium transition-colors ${
                    modalTarget === score
                      ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                      : 'border-gray-200 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                  }`}
                >
                  {score}
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowTargetModal(false)}
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                Отмена
              </button>
              <button
                onClick={handleSaveTarget}
                disabled={saving}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Сохраняем...' : 'Применить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
