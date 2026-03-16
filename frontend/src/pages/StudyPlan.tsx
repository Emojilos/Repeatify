import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

interface PlanData {
  target_score: number
  exam_date: string
  hours_per_day: number
  days_remaining: number
  total_hours: number
  study_hours: number
  review_hours: number
  tasks_to_study: number[]
  mastered_tasks: number[]
  warning: string | null
  weeks: Week[]
}

interface Week {
  week: number
  days: Day[]
}

interface Day {
  date: string
  study: StudyItem[]
  study_minutes: number
  review_minutes: number
}

interface StudyItem {
  task_number: number
  minutes: number
}

interface StudyPlanResponse {
  id: string
  user_id: string
  target_score: number
  exam_date: string
  hours_per_day: number
  plan_data: PlanData | null
  generated_at: string
  is_active: boolean
}

const TASK_COLORS: Record<number, string> = {
  1: 'bg-blue-400', 2: 'bg-blue-500', 3: 'bg-blue-600',
  4: 'bg-green-400', 5: 'bg-green-500', 6: 'bg-green-600',
  7: 'bg-purple-400', 8: 'bg-purple-500', 9: 'bg-purple-600',
  10: 'bg-orange-400', 11: 'bg-orange-500', 12: 'bg-orange-600',
  13: 'bg-red-400', 14: 'bg-red-500', 15: 'bg-pink-400',
  16: 'bg-pink-500', 17: 'bg-rose-500', 18: 'bg-amber-500', 19: 'bg-amber-600',
}

function taskColor(tn: number): string {
  return TASK_COLORS[tn] || 'bg-gray-400'
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function formatWeekRange(days: Day[]): string {
  if (days.length === 0) return ''
  const first = formatDate(days[0].date)
  const last = formatDate(days[days.length - 1].date)
  return `${first} — ${last}`
}

function pluralDays(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return `${n} день`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${n} дня`
  return `${n} дней`
}

function isToday(iso: string): boolean {
  return iso === new Date().toISOString().slice(0, 10)
}

function isPast(iso: string): boolean {
  return iso < new Date().toISOString().slice(0, 10)
}

const TARGET_OPTIONS = [70, 80, 90, 100] as const
const HOURS_OPTIONS = [0.5, 1, 1.5, 2, 3] as const

export default function StudyPlan() {
  const [plan, setPlan] = useState<StudyPlanResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [recalculating, setRecalculating] = useState(false)

  // Modal state
  const [modalTarget, setModalTarget] = useState(80)
  const [modalHours, setModalHours] = useState(1.5)
  const [modalExamDate, setModalExamDate] = useState('')

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
      setModalHours(data.hours_per_day)
      setModalExamDate(data.exam_date)
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

  async function handleRecalculate() {
    setRecalculating(true)
    try {
      const endpoint = plan ? '/api/study-plan/recalculate' : '/api/study-plan/generate'
      const method = plan ? 'PUT' : 'POST'
      const data = await api<StudyPlanResponse>(endpoint, {
        method,
        body: JSON.stringify({
          target_score: modalTarget,
          hours_per_day: modalHours,
          exam_date: modalExamDate,
        }),
      })
      setPlan(data)
      setShowModal(false)
    } catch (err: unknown) {
      setError((err as Error).message)
    } finally {
      setRecalculating(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-6 h-10 w-48 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="mb-6 h-24 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-4 text-2xl font-bold dark:text-gray-100">Мой план</h1>
        <p className="text-red-600">{error}</p>
      </div>
    )
  }

  // No plan yet
  if (!plan) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-2xl font-bold dark:text-gray-100">Мой план</h1>
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-800">
          <p className="mb-2 text-4xl">📋</p>
          <h2 className="mb-2 text-lg font-semibold dark:text-gray-100">План ещё не создан</h2>
          <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
            Пройдите диагностику и создайте персональный план подготовки
          </p>
          <Link
            to="/onboarding"
            className="inline-block rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Начать
          </Link>
        </div>
      </div>
    )
  }

  const pd = plan.plan_data
  if (!pd) return null

  // Compute current predicted score (simple: mastered tasks points)
  const POINTS: Record<number, number> = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
    7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1,
    13: 2, 14: 2, 15: 2, 16: 2, 17: 2, 18: 4, 19: 4,
  }
  const masteredPoints = pd.mastered_tasks.reduce((sum, tn) => sum + (POINTS[tn] || 0), 0)
  const totalPossible = pd.tasks_to_study.reduce((sum, tn) => sum + (POINTS[tn] || 0), 0) + masteredPoints

  // Find unique task_numbers across weeks for legend
  const allTaskNumbers = new Set<number>()
  pd.weeks.forEach(w => w.days.forEach(d => d.study.forEach(s => allTaskNumbers.add(s.task_number))))

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold dark:text-gray-100">Мой план</h1>
        <button
          onClick={() => setShowModal(true)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          Пересчитать план
        </button>
      </div>

      {/* Warning */}
      {pd.warning && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-900/30">
          <p className="text-sm text-amber-700 dark:text-amber-300">{pd.warning}</p>
        </div>
      )}

      {/* Stats summary */}
      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Целевой балл</p>
          <p className="text-2xl font-bold text-blue-600">{pd.target_score}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">До экзамена</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{pluralDays(pd.days_remaining)}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Часов в день</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{pd.hours_per_day}ч</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Освоено</p>
          <p className="text-2xl font-bold text-green-600">{masteredPoints}/{totalPossible}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">баллов</p>
        </div>
      </div>

      {/* Mastered tasks */}
      {pd.mastered_tasks.length > 0 && (
        <div className="mb-6 rounded-xl border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/30">
          <p className="mb-2 text-sm font-medium text-green-800 dark:text-green-200">
            Освоенные задания (пропущены в плане):
          </p>
          <div className="flex flex-wrap gap-2">
            {pd.mastered_tasks.map(tn => (
              <span key={tn} className="rounded-lg bg-green-200 px-2.5 py-1 text-xs font-semibold text-green-800 dark:bg-green-800 dark:text-green-200">
                #{tn}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mb-4 flex flex-wrap gap-2">
        {Array.from(allTaskNumbers).sort((a, b) => a - b).map(tn => (
          <span key={tn} className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
            <span className={`inline-block h-3 w-3 rounded ${taskColor(tn)}`} />
            Задание {tn}
          </span>
        ))}
      </div>

      {/* Weekly timeline */}
      <div className="space-y-4">
        {pd.weeks.map(week => (
          <div key={week.week} className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
            <div className="border-b border-gray-100 px-5 py-3 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Неделя {week.week}
                </h3>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {formatWeekRange(week.days)}
                </span>
              </div>
            </div>
            <div className="divide-y divide-gray-50 dark:divide-gray-700/50">
              {week.days.map(day => {
                const today = isToday(day.date)
                const past = isPast(day.date)
                return (
                  <div
                    key={day.date}
                    className={`flex items-center gap-4 px-5 py-3 ${
                      today ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                    } ${past ? 'opacity-50' : ''}`}
                  >
                    <div className="w-20 shrink-0">
                      <p className={`text-sm font-medium ${today ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'}`}>
                        {formatDate(day.date)}
                      </p>
                      {today && <p className="text-[10px] font-semibold text-blue-500">СЕГОДНЯ</p>}
                    </div>

                    {/* Study blocks as colored bar segments */}
                    <div className="flex-1">
                      {day.study.length > 0 ? (
                        <div className="flex gap-1">
                          {day.study.map((item, idx) => {
                            const totalMinutes = day.study_minutes || 1
                            const widthPercent = Math.max((item.minutes / totalMinutes) * 100, 8)
                            return (
                              <div
                                key={idx}
                                className={`${taskColor(item.task_number)} flex items-center justify-center rounded px-2 py-1.5 text-[10px] font-semibold text-white`}
                                style={{ width: `${widthPercent}%` }}
                                title={`Задание ${item.task_number}: ${item.minutes} мин`}
                              >
                                {item.task_number}
                              </div>
                            )
                          })}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-400 dark:text-gray-500">Повторение</p>
                      )}
                    </div>

                    <div className="w-24 shrink-0 text-right">
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {day.study_minutes > 0 && <span>{day.study_minutes}мин учёба</span>}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500">
                        {day.review_minutes}мин повт.
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Recalculate Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowModal(false)}>
          <div
            className="mx-4 w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-800"
            onClick={e => e.stopPropagation()}
          >
            <h2 className="mb-5 text-lg font-bold dark:text-gray-100">Пересчитать план</h2>

            {/* Target score */}
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Целевой балл
              </label>
              <div className="grid grid-cols-4 gap-2">
                {TARGET_OPTIONS.map(score => (
                  <button
                    key={score}
                    onClick={() => setModalTarget(score)}
                    className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                      modalTarget === score
                        ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                        : 'border-gray-200 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                    }`}
                  >
                    {score}
                  </button>
                ))}
              </div>
            </div>

            {/* Hours per day */}
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Часов в день
              </label>
              <div className="grid grid-cols-5 gap-2">
                {HOURS_OPTIONS.map(h => (
                  <button
                    key={h}
                    onClick={() => setModalHours(h)}
                    className={`rounded-lg border px-2 py-2 text-sm font-medium transition-colors ${
                      modalHours === h
                        ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                        : 'border-gray-200 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
                    }`}
                  >
                    {h}ч
                  </button>
                ))}
              </div>
            </div>

            {/* Exam date */}
            <div className="mb-6">
              <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Дата экзамена
              </label>
              <input
                type="date"
                value={modalExamDate}
                onChange={e => setModalExamDate(e.target.value)}
                min={new Date().toISOString().slice(0, 10)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                Отмена
              </button>
              <button
                onClick={handleRecalculate}
                disabled={recalculating}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
              >
                {recalculating ? 'Пересчёт...' : 'Применить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
