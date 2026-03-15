import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
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

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function strengthColor(s: number): string {
  if (s >= 70) return 'text-green-600'
  if (s >= 40) return 'text-yellow-600'
  if (s > 0) return 'text-orange-600'
  return 'text-gray-400 dark:text-gray-500'
}

function strengthBg(s: number): string {
  if (s >= 70) return 'bg-green-100 dark:bg-green-900/40'
  if (s >= 40) return 'bg-yellow-100 dark:bg-yellow-900/40'
  if (s > 0) return 'bg-orange-100 dark:bg-orange-900/40'
  return 'bg-gray-50 dark:bg-gray-800'
}

function actionColor(action: string): string {
  if (action.includes('FIRe')) return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
  if (action.includes('\u0442\u0435\u043E\u0440\u0438\u044E')) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
  return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
}

function buildHeatmapData(activities: DailyActivity[]) {
  const activityMap = new Map<string, number>()
  for (const a of activities) {
    activityMap.set(a.date, a.problems_solved)
  }

  const today = new Date()
  const weeks: { date: Date; count: number }[][] = []
  const start = new Date(today)
  start.setDate(start.getDate() - 363)
  while (start.getDay() !== 1) {
    start.setDate(start.getDate() - 1)
  }

  let currentWeek: { date: Date; count: number }[] = []
  const cursor = new Date(start)
  while (cursor <= today) {
    const key = cursor.toISOString().slice(0, 10)
    currentWeek.push({ date: new Date(cursor), count: activityMap.get(key) ?? 0 })
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

const MONTH_LABELS = [
  '\u042F\u043D\u0432', '\u0424\u0435\u0432', '\u041C\u0430\u0440', '\u0410\u043F\u0440', '\u041C\u0430\u0439', '\u0418\u044E\u043D',
  '\u0418\u044E\u043B', '\u0410\u0432\u0433', '\u0421\u0435\u043D', '\u041E\u043A\u0442', '\u041D\u043E\u044F', '\u0414\u0435\u043A',
]

function buildChartData(activities: DailyActivity[], days: number) {
  const today = new Date()
  const since = new Date(today)
  since.setDate(since.getDate() - days + 1)

  const activityMap = new Map<string, number>()
  for (const a of activities) {
    activityMap.set(a.date, a.problems_solved)
  }

  const result: { date: string; label: string; solved: number }[] = []
  const cursor = new Date(since)
  while (cursor <= today) {
    const key = cursor.toISOString().slice(0, 10)
    const day = cursor.getDate()
    const month = cursor.getMonth()
    result.push({
      date: key,
      label: `${day}.${String(month + 1).padStart(2, '0')}`,
      solved: activityMap.get(key) ?? 0,
    })
    cursor.setDate(cursor.getDate() + 1)
  }
  return result
}

/* ------------------------------------------------------------------ */
/*  Component                                                         */
/* ------------------------------------------------------------------ */

export default function Progress() {
  const [gapMap, setGapMap] = useState<GapMapEntry[]>([])
  const [calendar, setCalendar] = useState<ActivityCalendarResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [filterTask, setFilterTask] = useState<string>('')
  const [filterMinStr, setFilterMinStr] = useState<string>('')
  const [filterMaxStr, setFilterMaxStr] = useState<string>('')
  const [chartDays, setChartDays] = useState<7 | 30>(7)

  useEffect(() => {
    Promise.all([
      api<GapMapResponse>('/api/progress/gap-map'),
      api<ActivityCalendarResponse>('/api/progress/activity-calendar'),
    ])
      .then(([gm, cal]) => {
        setGapMap(gm.entries)
        setCalendar(cal)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">Прогресс</h1>
        <div className="space-y-6">
          <div className="h-64 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
          <div className="h-40 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
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

  const filtered = gapMap.filter((e) => {
    if (filterTask && e.task_number !== Number(filterTask)) return false
    if (filterMinStr && e.strength < Number(filterMinStr)) return false
    if (filterMaxStr && e.strength > Number(filterMaxStr)) return false
    return true
  })

  const heatmapWeeks = calendar ? buildHeatmapData(calendar.activities) : []
  const chartData = calendar ? buildChartData(calendar.activities, chartDays) : []

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">Прогресс</h1>

      {/* ====== Section 1: Gap Map ====== */}
      <section className="mb-8">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">Карта пробелов</h2>

        <div className="mb-4 flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Номер задания</label>
            <select
              value={filterTask}
              onChange={(e) => setFilterTask(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            >
              <option value="">Все</option>
              {Array.from({ length: 19 }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  Задание {i + 1}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Сила от (%)</label>
            <input
              type="number"
              min={0}
              max={100}
              value={filterMinStr}
              onChange={(e) => setFilterMinStr(e.target.value)}
              placeholder="0"
              className="w-20 rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Сила до (%)</label>
            <input
              type="number"
              min={0}
              max={100}
              value={filterMaxStr}
              onChange={(e) => setFilterMaxStr(e.target.value)}
              placeholder="100"
              className="w-20 rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>
          {(filterTask || filterMinStr || filterMaxStr) && (
            <button
              onClick={() => { setFilterTask(''); setFilterMinStr(''); setFilterMaxStr('') }}
              className="text-sm text-blue-600 hover:underline"
            >
              Сбросить
            </button>
          )}
        </div>

        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">#</th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">Тема</th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">Сила</th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">Ошибки (30д)</th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">Посл. ошибка</th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">Рекомендация</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400 dark:text-gray-500">
                    Нет данных по заданным фильтрам
                  </td>
                </tr>
              ) : (
                filtered.map((e) => (
                  <tr key={e.task_number} className="border-b border-gray-100 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700">
                    <td className="px-4 py-3">
                      <Link
                        to={`/topics`}
                        className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-xs font-bold text-white"
                      >
                        {e.task_number}
                      </Link>
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{e.topic}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className={`rounded-full px-2 py-0.5 text-xs font-semibold ${strengthBg(e.strength)} ${strengthColor(e.strength)}`}>
                          {e.strength}%
                        </div>
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                          <div
                            className={`h-full rounded-full transition-all ${
                              e.strength >= 70 ? 'bg-green-500' : e.strength >= 40 ? 'bg-yellow-500' : e.strength > 0 ? 'bg-orange-500' : 'bg-gray-300 dark:bg-gray-600'
                            }`}
                            style={{ width: `${e.strength}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {e.error_count > 0 ? (
                        <span className="font-medium text-red-600">{e.error_count}</span>
                      ) : (
                        <span className="text-gray-400 dark:text-gray-500">0</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                      {e.last_error_date ?? '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${actionColor(e.recommended_action)}`}>
                        {e.recommended_action}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* ====== Section 2: Activity Heatmap ====== */}
      <section className="mb-8">
        <div className="mb-4 flex items-center justify-between">
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

          {['\u041F\u043D', '', '\u0421\u0440', '', '\u041F\u0442', '', ''].map((dayLabel, dayIdx) => (
            <div key={dayIdx} className="flex items-center">
              <div className="w-8 shrink-0 text-[10px] text-gray-400 dark:text-gray-500">{dayLabel}</div>
              {heatmapWeeks.map((week, wi) => {
                const cell = week[dayIdx]
                if (!cell) return <div key={wi} style={{ width: 14, height: 14, margin: 1 }} />
                const isFuture = cell.date > new Date()
                return (
                  <div
                    key={wi}
                    title={`${cell.date.toISOString().slice(0, 10)}: ${cell.count} задач`}
                    className={`rounded-sm ${isFuture ? 'bg-transparent' : heatmapCellColor(cell.count)}`}
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

      {/* ====== Section 3: Activity Chart ====== */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Динамика решений</h2>
          <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 dark:border-gray-700">
            <button
              onClick={() => setChartDays(7)}
              className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                chartDays === 7
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
              }`}
            >
              7 дней
            </button>
            <button
              onClick={() => setChartDays(30)}
              className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                chartDays === 30
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
              }`}
            >
              30 дней
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11 }}
                  interval={chartDays === 30 ? 4 : 0}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip
                  formatter={(value) => [`${value} задач`, 'Решено']}
                  labelFormatter={(label) => `Дата: ${label}`}
                />
                <Bar
                  dataKey="solved"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={chartDays === 30 ? 16 : 40}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-64 items-center justify-center text-gray-400 dark:text-gray-500">
              Нет данных для отображения
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
