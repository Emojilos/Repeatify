import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface GapMapEntry {
  task_number: number
  topic: string
  strength: number
  error_count: number
  last_error_date: string | null
  recommended_action: string
}

interface GapMapResponse {
  entries: GapMapEntry[]
}

interface DailyActivity {
  date: string
  sessions_completed: number
  problems_solved: number
  xp_earned: number
  streak_maintained: boolean
}

interface ActivityCalendarResponse {
  activities: DailyActivity[]
  current_streak: number
  longest_streak: number
}

interface TaskRetrievability {
  task_number: number
  avg_retrievability: number
  cards_count: number
}

interface FSRSStatsResponse {
  total_cards: number
  cards_in_review: number
  avg_stability: number
  cards_due_today: number
  retrievability_by_task: TaskRetrievability[]
}

interface DashboardResponse {
  exam_countdown: number | null
  today_review_count: number
  weekly_stats: { problems_solved: number; problems_correct: number }
  recommendations: string[]
  current_xp: number
  current_level: number
  current_streak: number
}

interface PriorityTopic {
  task_number: number
  title: string
  max_points: number
  strength_score: number
  fire_completed: boolean
  priority_score: number
  recommended_action: string
}

interface ExamReadinessResponse {
  readiness_percent: number
  exam_countdown: number | null
  priority_topics: PriorityTopic[]
  summary: string
}

interface TaskScoreBreakdown {
  cards_count: number
  avg_retrievability: number
  is_mastered: boolean
  points: number
}

interface PredictedScoreResponse {
  predicted_primary_score: number
  predicted_test_score: number
  breakdown: Record<number, TaskScoreBreakdown>
}


/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function strengthColor(s: number): string {
  if (s >= 70) return 'text-green-600'
  if (s >= 40) return 'text-yellow-600'
  if (s > 0) return 'text-orange-600'
  return 'text-gray-400 dark:text-gray-500'
}

function strengthBarColor(s: number): string {
  if (s >= 70) return 'bg-green-500'
  if (s >= 40) return 'bg-yellow-500'
  if (s > 0) return 'bg-orange-500'
  return 'bg-gray-300 dark:bg-gray-600'
}

function actionColor(action: string): string {
  if (action.includes('Изучить')) return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
  if (action.includes('Повторить')) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
  if (action.includes('Закрепить')) return 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
  return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
}

function buildHeatmapData(activities: DailyActivity[]) {
  const activityMap = new Map<string, DailyActivity>()
  for (const a of activities) {
    activityMap.set(a.date, a)
  }

  const today = new Date()
  const weeks: { date: Date; activity: DailyActivity | null }[][] = []
  const start = new Date(today)
  start.setDate(start.getDate() - 363)
  while (start.getDay() !== 1) {
    start.setDate(start.getDate() - 1)
  }

  let currentWeek: { date: Date; activity: DailyActivity | null }[] = []
  const cursor = new Date(start)
  while (cursor <= today) {
    const key = cursor.toISOString().slice(0, 10)
    currentWeek.push({ date: new Date(cursor), activity: activityMap.get(key) ?? null })
    if (currentWeek.length === 7) {
      weeks.push(currentWeek)
      currentWeek = []
    }
    cursor.setDate(cursor.getDate() + 1)
  }
  if (currentWeek.length > 0) {
    weeks.push(currentWeek)
  }
  return weeks
}

function heatmapCellColor(count: number): string {
  if (count === 0) return 'bg-gray-100 dark:bg-gray-800'
  if (count <= 2) return 'bg-green-200 dark:bg-green-800'
  if (count <= 5) return 'bg-green-400 dark:bg-green-600'
  if (count <= 10) return 'bg-green-500'
  return 'bg-green-700'
}

const MONTH_LABELS = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

function buildChartData(activities: DailyActivity[], days: number) {
  const today = new Date()
  const since = new Date(today)
  since.setDate(since.getDate() - days + 1)

  const activityMap = new Map<string, DailyActivity>()
  for (const a of activities) {
    activityMap.set(a.date, a)
  }

  const result: { date: string; label: string; solved: number; xp: number }[] = []
  const cursor = new Date(since)
  while (cursor <= today) {
    const key = cursor.toISOString().slice(0, 10)
    const act = activityMap.get(key)
    result.push({
      date: key,
      label: `${cursor.getDate()}.${String(cursor.getMonth() + 1).padStart(2, '0')}`,
      solved: act?.problems_solved ?? 0,
      xp: act?.xp_earned ?? 0,
    })
    cursor.setDate(cursor.getDate() + 1)
  }
  return result
}

function readinessGradient(pct: number): string {
  if (pct >= 80) return 'from-green-500 to-emerald-500'
  if (pct >= 60) return 'from-blue-500 to-cyan-500'
  if (pct >= 40) return 'from-yellow-500 to-amber-500'
  return 'from-orange-500 to-red-500'
}

/* ------------------------------------------------------------------ */
/*  Component                                                         */
/* ------------------------------------------------------------------ */

export default function Progress() {
  const [gapMap, setGapMap] = useState<GapMapEntry[]>([])
  const [calendar, setCalendar] = useState<ActivityCalendarResponse | null>(null)
  const [fsrsStats, setFsrsStats] = useState<FSRSStatsResponse | null>(null)
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [readiness, setReadiness] = useState<ExamReadinessResponse | null>(null)
  const [predicted, setPredicted] = useState<PredictedScoreResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [chartDays, setChartDays] = useState<7 | 30>(7)
  const [chartMode, setChartMode] = useState<'solved' | 'xp'>('solved')
  const [gapSort, setGapSort] = useState<'strength' | 'errors'>('strength')
  const [showAllGap, setShowAllGap] = useState(false)

  useEffect(() => {
    Promise.all([
      api<GapMapResponse>('/api/progress/gap-map'),
      api<ActivityCalendarResponse>('/api/progress/activity-calendar'),
      api<FSRSStatsResponse>('/api/progress/fsrs-stats'),
      api<DashboardResponse>('/api/progress/dashboard'),
      api<ExamReadinessResponse>('/api/progress/exam-readiness'),
      api<PredictedScoreResponse>('/api/progress/predicted-score').catch(() => null),
    ])
      .then(([gm, cal, fs, db, er, ps]) => {
        setGapMap(gm.entries)
        setCalendar(cal)
        setFsrsStats(fs)
        setDashboard(db)
        setReadiness(er)
        if (ps) setPredicted(ps)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">Прогресс</h1>
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
            ))}
          </div>
          <div className="h-48 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
          <div className="h-64 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-4 text-2xl font-bold text-gray-900 dark:text-gray-100">Прогресс</h1>
        <p className="text-red-600">Ошибка загрузки: {error}</p>
      </div>
    )
  }

  const heatmapWeeks = calendar ? buildHeatmapData(calendar.activities) : []
  const chartData = calendar ? buildChartData(calendar.activities, chartDays) : []

  const totalXpWeek = chartData.reduce((s, d) => s + d.xp, 0)
  const totalSolvedWeek = chartData.reduce((s, d) => s + d.solved, 0)

  const sortedGap = [...gapMap].sort((a, b) => {
    if (gapSort === 'errors') return b.error_count - a.error_count
    return a.strength - b.strength
  })
  const visibleGap = showAllGap ? sortedGap : sortedGap.slice(0, 8)

  const weeklyAccuracy = dashboard && dashboard.weekly_stats.problems_solved > 0
    ? Math.round((dashboard.weekly_stats.problems_correct / dashboard.weekly_stats.problems_solved) * 100)
    : null

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Прогресс</h1>

      {/* ====== Overview Cards ====== */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {dashboard && (
          <>
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-1 text-xs text-gray-500 dark:text-gray-400">Уровень</div>
              <div className="text-3xl font-bold text-blue-600">{dashboard.current_level}</div>
              <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">{dashboard.current_xp} XP</div>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-1 text-xs text-gray-500 dark:text-gray-400">Серия</div>
              <div className="text-3xl font-bold text-orange-500">{dashboard.current_streak}</div>
              <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">
                макс. {calendar?.longest_streak ?? 0}
              </div>
            </div>
            {dashboard.exam_countdown !== null && (
              <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <div className="mb-1 text-xs text-gray-500 dark:text-gray-400">До экзамена</div>
                <div className={`text-3xl font-bold ${dashboard.exam_countdown <= 14 ? 'text-red-600' : dashboard.exam_countdown <= 30 ? 'text-yellow-600' : 'text-gray-900 dark:text-gray-100'}`}>
                  {dashboard.exam_countdown}
                </div>
                <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">дней</div>
              </div>
            )}
          </>
        )}
        {predicted && (
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="mb-1 text-xs text-gray-500 dark:text-gray-400">Прогноз балла</div>
            <div className="text-3xl font-bold text-purple-600">{predicted.predicted_test_score}</div>
            <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">
              перв. {predicted.predicted_primary_score}
            </div>
          </div>
        )}
        {fsrsStats && (
          <>
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-1 text-xs text-gray-500 dark:text-gray-400">К повторению</div>
              <div className={`text-3xl font-bold ${fsrsStats.cards_due_today > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                {fsrsStats.cards_due_today}
              </div>
              <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">сегодня</div>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-1 text-xs text-gray-500 dark:text-gray-400">Точность (7д)</div>
              <div className="text-3xl font-bold text-green-600">{weeklyAccuracy !== null ? `${weeklyAccuracy}%` : '-'}</div>
              <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">
                {dashboard?.weekly_stats.problems_correct ?? 0}/{dashboard?.weekly_stats.problems_solved ?? 0} задач
              </div>
            </div>
          </>
        )}
      </div>

      {/* ====== Exam Readiness ====== */}
      {readiness && (
        <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
            {/* Readiness circle */}
            <div className="flex flex-col items-center gap-2">
              <div className="relative flex h-32 w-32 items-center justify-center">
                <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="52" fill="none" stroke="currentColor" strokeWidth="8"
                    className="text-gray-100 dark:text-gray-700" />
                  <circle cx="60" cy="60" r="52" fill="none" strokeWidth="8" strokeLinecap="round"
                    strokeDasharray={`${readiness.readiness_percent * 3.267} 326.7`}
                    className={`bg-gradient-to-r ${readinessGradient(readiness.readiness_percent)}`}
                    style={{
                      stroke: readiness.readiness_percent >= 80 ? '#22c55e'
                        : readiness.readiness_percent >= 60 ? '#3b82f6'
                        : readiness.readiness_percent >= 40 ? '#eab308'
                        : '#f97316'
                    }}
                  />
                </svg>
                <div className="absolute text-center">
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {Math.round(readiness.readiness_percent)}%
                  </div>
                  <div className="text-[10px] text-gray-500 dark:text-gray-400">готовность</div>
                </div>
              </div>
              <p className="max-w-xs text-center text-xs text-gray-500 dark:text-gray-400">{readiness.summary}</p>
            </div>

            {/* Priority topics */}
            <div className="flex-1">
              <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">Приоритетные темы</h3>
              <div className="space-y-2">
                {readiness.priority_topics.map((t) => (
                  <div key={t.task_number} className="flex items-center gap-3 rounded-lg border border-gray-100 bg-gray-50 px-3 py-2 dark:border-gray-700 dark:bg-gray-800/50">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-xs font-bold text-white">
                      {t.task_number}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{t.title}</div>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-20 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                          <div className={`h-full rounded-full ${strengthBarColor(t.strength_score * 100)}`}
                            style={{ width: `${t.strength_score * 100}%` }} />
                        </div>
                        <span className="text-xs text-gray-400 dark:text-gray-500">{Math.round(t.strength_score * 100)}%</span>
                      </div>
                    </div>
                    <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${actionColor(t.recommended_action)}`}>
                      {t.recommended_action}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {dashboard && dashboard.recommendations.length > 0 && (
            <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-3 dark:border-blue-900 dark:bg-blue-900/20">
              <div className="mb-1 text-xs font-semibold text-blue-700 dark:text-blue-300">Рекомендации</div>
              <ul className="space-y-1">
                {dashboard.recommendations.map((r, i) => (
                  <li key={i} className="text-xs text-blue-600 dark:text-blue-400">{r}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {/* ====== Predicted Score Breakdown ====== */}
      {predicted && Object.keys(predicted.breakdown).length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-gray-100">Прогноз по заданиям</h2>
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <div className="flex items-end gap-1 p-4" style={{ height: 200 }}>
              {Array.from({ length: 19 }, (_, i) => i + 1).map((tn) => {
                const entry = predicted.breakdown[tn]
                const maxPts = entry?.points ?? 0
                const r = entry ? Math.round(entry.avg_retrievability * 100) : 0
                const mastered = entry?.is_mastered ?? false
                return (
                  <div key={tn} className="flex flex-1 flex-col items-center gap-1">
                    <span className="text-[9px] text-gray-500 dark:text-gray-400">
                      {maxPts > 0 ? `${maxPts}б` : '-'}
                    </span>
                    <div className="w-full flex-1 flex flex-col justify-end">
                      <div
                        className={`w-full rounded-t transition-all ${mastered ? 'bg-green-500' : r >= 50 ? 'bg-blue-500' : r > 0 ? 'bg-orange-400' : 'bg-gray-200 dark:bg-gray-700'}`}
                        style={{ height: `${Math.max(r, 2)}%` }}
                        title={`Задание ${tn}: ${r}% retrievability, ${maxPts} баллов`}
                      />
                    </div>
                    <span className={`text-[10px] font-medium ${mastered ? 'text-green-600' : 'text-gray-500 dark:text-gray-400'}`}>{tn}</span>
                  </div>
                )
              })}
            </div>
            <div className="flex items-center gap-4 border-t border-gray-100 px-4 py-2 text-[10px] text-gray-400 dark:border-gray-700 dark:text-gray-500">
              <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-sm bg-green-500" /> Освоено</span>
              <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-sm bg-blue-500" /> В процессе</span>
              <span className="flex items-center gap-1"><span className="inline-block h-2 w-2 rounded-sm bg-orange-400" /> Слабо</span>
            </div>
          </div>
        </section>
      )}

      {/* ====== Activity Heatmap ====== */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Активность</h2>
          {calendar && (
            <div className="flex gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span>Серия: <strong className="text-gray-900 dark:text-gray-100">{calendar.current_streak}</strong></span>
              <span>Макс: <strong className="text-gray-900 dark:text-gray-100">{calendar.longest_streak}</strong></span>
            </div>
          )}
        </div>

        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="mb-1 flex">
            <div className="w-8 shrink-0" />
            {heatmapWeeks.map((week, wi) => {
              const firstDay = week[0]
              if (!firstDay) return null
              const prevWeek = heatmapWeeks[wi - 1]
              const prevMonth = prevWeek?.[0]?.date.getMonth()
              const curMonth = firstDay.date.getMonth()
              if (wi === 0 || curMonth !== prevMonth) {
                return (
                  <div key={wi} className="text-[10px] text-gray-400 dark:text-gray-500" style={{ width: 14, marginRight: 2 }}>
                    {MONTH_LABELS[curMonth]}
                  </div>
                )
              }
              return <div key={wi} style={{ width: 14, marginRight: 2 }} />
            })}
          </div>

          {['Пн', '', 'Ср', '', 'Пт', '', ''].map((dayLabel, dayIdx) => (
            <div key={dayIdx} className="flex items-center">
              <div className="w-8 shrink-0 text-[10px] text-gray-400 dark:text-gray-500">{dayLabel}</div>
              {heatmapWeeks.map((week, wi) => {
                const cell = week[dayIdx]
                if (!cell) return <div key={wi} style={{ width: 14, height: 14, margin: 1 }} />
                const isFuture = cell.date > new Date()
                const count = cell.activity?.problems_solved ?? 0
                return (
                  <div
                    key={wi}
                    title={`${cell.date.toISOString().slice(0, 10)}: ${count} задач`}
                    className={`rounded-sm ${isFuture ? 'bg-transparent' : heatmapCellColor(count)}`}
                    style={{ width: 12, height: 12, margin: 1 }}
                  />
                )
              })}
            </div>
          ))}

          <div className="mt-3 flex items-center justify-end gap-1 text-[10px] text-gray-400 dark:text-gray-500">
            <span>Меньше</span>
            <div className="h-3 w-3 rounded-sm bg-gray-100 dark:bg-gray-800" />
            <div className="h-3 w-3 rounded-sm bg-green-200 dark:bg-green-800" />
            <div className="h-3 w-3 rounded-sm bg-green-400 dark:bg-green-600" />
            <div className="h-3 w-3 rounded-sm bg-green-500" />
            <div className="h-3 w-3 rounded-sm bg-green-700" />
            <span>Больше</span>
          </div>
        </div>
      </section>

      {/* ====== Activity Chart ====== */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Динамика</h2>
            <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 dark:border-gray-700">
              <button
                onClick={() => setChartMode('solved')}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  chartMode === 'solved' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                Задачи
              </button>
              <button
                onClick={() => setChartMode('xp')}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  chartMode === 'xp' ? 'bg-purple-600 text-white' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                XP
              </button>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Итого: <strong className="text-gray-900 dark:text-gray-100">{chartMode === 'solved' ? totalSolvedWeek : totalXpWeek}</strong>
              {chartMode === 'solved' ? ' задач' : ' XP'}
            </span>
            <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 dark:border-gray-700">
              <button
                onClick={() => setChartDays(7)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  chartDays === 7 ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                7д
              </button>
              <button
                onClick={() => setChartDays(30)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  chartDays === 30 ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                30д
              </button>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          {chartData.length > 0 ? (
            <div>
              <div className="flex items-end gap-px" style={{ height: 200 }}>
                {chartData.map((d) => {
                  const values = chartData.map(x => chartMode === 'solved' ? x.solved : x.xp)
                  const maxVal = Math.max(...values, 1)
                  const val = chartMode === 'solved' ? d.solved : d.xp
                  const pct = (val / maxVal) * 100
                  const barColor = chartMode === 'solved' ? 'bg-blue-500' : 'bg-purple-500'
                  return (
                    <div key={d.date} className="flex flex-1 flex-col items-center justify-end" style={{ height: '100%' }}>
                      {val > 0 && (
                        <span className="mb-1 text-[9px] text-gray-500 dark:text-gray-400">{val}</span>
                      )}
                      <div
                        className={`w-full rounded-t ${barColor} transition-all`}
                        style={{ height: `${Math.max(pct, val > 0 ? 4 : 0)}%` }}
                        title={`${d.label}: ${val} ${chartMode === 'solved' ? 'задач' : 'XP'}`}
                      />
                    </div>
                  )
                })}
              </div>
              <div className="mt-1 flex gap-px">
                {chartData.map((d, i) => (
                  <div key={d.date} className="flex-1 text-center text-[9px] text-gray-400 dark:text-gray-500">
                    {chartDays === 30 ? (i % 5 === 0 ? d.label : '') : d.label}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex h-48 items-center justify-center text-gray-400 dark:text-gray-500">
              Нет данных для отображения
            </div>
          )}
        </div>
      </section>

      {/* ====== FSRS Retrievability ====== */}
      {fsrsStats && fsrsStats.retrievability_by_task.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-gray-100">Запоминание по заданиям</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5">
            {fsrsStats.retrievability_by_task.map((t) => {
              const pct = Math.round(t.avg_retrievability * 100)
              const ring = pct >= 80 ? 'border-green-400' : pct >= 50 ? 'border-blue-400' : pct > 0 ? 'border-orange-400' : 'border-gray-200 dark:border-gray-700'
              return (
                <div key={t.task_number} className={`rounded-xl border-2 ${ring} bg-white p-3 text-center dark:bg-gray-800`}>
                  <div className="mb-1 text-xs text-gray-400 dark:text-gray-500">Задание {t.task_number}</div>
                  <div className={`text-2xl font-bold ${pct >= 80 ? 'text-green-600' : pct >= 50 ? 'text-blue-600' : pct > 0 ? 'text-orange-600' : 'text-gray-400'}`}>
                    {pct}%
                  </div>
                  <div className="text-[10px] text-gray-400 dark:text-gray-500">{t.cards_count} карт.</div>
                </div>
              )
            })}
          </div>
          <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-center dark:border-gray-700 dark:bg-gray-800">
              <div className="text-lg font-bold text-gray-900 dark:text-gray-100">{fsrsStats.total_cards}</div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400">Всего карточек</div>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-center dark:border-gray-700 dark:bg-gray-800">
              <div className="text-lg font-bold text-blue-600">{fsrsStats.cards_in_review}</div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400">На повторении</div>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-center dark:border-gray-700 dark:bg-gray-800">
              <div className="text-lg font-bold text-gray-900 dark:text-gray-100">{fsrsStats.avg_stability}д</div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400">Ср. стабильность</div>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-center dark:border-gray-700 dark:bg-gray-800">
              <div className={`text-lg font-bold ${fsrsStats.cards_due_today > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                {fsrsStats.cards_due_today}
              </div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400">К повторению</div>
            </div>
          </div>
        </section>
      )}

      {/* ====== Gap Map ====== */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Карта пробелов</h2>
          <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 dark:border-gray-700">
            <button
              onClick={() => setGapSort('strength')}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                gapSort === 'strength' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
              }`}
            >
              По силе
            </button>
            <button
              onClick={() => setGapSort('errors')}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                gapSort === 'errors' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
              }`}
            >
              По ошибкам
            </button>
          </div>
        </div>

        <div className="space-y-2">
          {visibleGap.map((e) => (
            <div key={e.task_number} className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <Link
                to="/topics"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white"
              >
                {e.task_number}
              </Link>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{e.topic}</span>
                  {e.error_count > 0 && (
                    <span className="shrink-0 rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-medium text-red-700 dark:bg-red-900/40 dark:text-red-300">
                      {e.error_count} ош.
                    </span>
                  )}
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                    <div className={`h-full rounded-full transition-all ${strengthBarColor(e.strength)}`}
                      style={{ width: `${Math.max(e.strength, 1)}%` }} />
                  </div>
                  <span className={`text-xs font-semibold ${strengthColor(e.strength)}`}>{e.strength}%</span>
                </div>
              </div>
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${actionColor(e.recommended_action)}`}>
                {e.recommended_action}
              </span>
            </div>
          ))}
        </div>

        {sortedGap.length > 8 && (
          <button
            onClick={() => setShowAllGap(!showAllGap)}
            className="mt-3 w-full rounded-lg border border-gray-200 bg-white py-2 text-sm font-medium text-blue-600 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700"
          >
            {showAllGap ? 'Свернуть' : `Показать все (${sortedGap.length})`}
          </button>
        )}
      </section>
    </div>
  )
}
