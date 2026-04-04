import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface UserStats {
  current_xp: number
  current_level: number
  current_streak: number
  longest_streak: number
  total_problems_solved: number
}

interface SavedVariant {
  id: string
  name: string
  task_number: number
  problem_count: number
  seed: number
  created_at: string
}

interface DailyActivity {
  date: string
  problems_solved: number
}

interface ActivityCalendarResponse {
  activities: DailyActivity[]
  current_streak: number
  longest_streak: number
}

/* Level table matching backend xp_service.py */
const LEVEL_TABLE: [number, number, string][] = [
  [0, 1, 'Новичок'],
  [100, 2, 'Ученик'],
  [300, 3, 'Практикант'],
  [600, 4, 'Решатель'],
  [1000, 5, 'Знаток'],
  [1500, 6, 'Эксперт'],
  [2500, 7, 'Мастер'],
  [4000, 8, 'Гуру'],
  [6000, 9, 'Легенда'],
  [10000, 10, 'Бог ЕГЭ'],
]

/* Score conversion table from PRD */
const SCORE_TABLE = [
  { primary: '0–6', score100: '0–23' },
  { primary: '7–11', score100: '24–39' },
  { primary: '12–14', score100: '40–56' },
  { primary: '15–17', score100: '57–70' },
  { primary: '18–20', score100: '71–80' },
  { primary: '21–24', score100: '81–90' },
  { primary: '25–29', score100: '91–98' },
  { primary: '30–31', score100: '99–100' },
]

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function levelName(level: number): string {
  const entry = LEVEL_TABLE.find(([, num]) => num === level)
  return entry ? entry[2] : 'Новичок'
}

function xpForNextLevel(currentXp: number): number | null {
  for (const [minXp] of LEVEL_TABLE) {
    if (currentXp < minXp) return minXp
  }
  return null
}

function xpForCurrentLevel(currentXp: number): number {
  let prev = 0
  for (const [minXp] of LEVEL_TABLE) {
    if (currentXp < minXp) return prev
    prev = minXp
  }
  return prev
}

/** Build a compact heatmap grid (last 16 weeks). */
function buildMiniHeatmap(activities: DailyActivity[]) {
  const activityMap = new Map<string, number>()
  for (const a of activities) {
    activityMap.set(a.date, a.problems_solved)
  }

  const today = new Date()
  const weeks: { date: Date; count: number }[][] = []
  const start = new Date(today)
  start.setDate(start.getDate() - 16 * 7 + 1)
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
  if (currentWeek.length > 0) weeks.push(currentWeek)
  return weeks
}

function heatmapCellColor(count: number): string {
  if (count === 0) return 'bg-gray-100 dark:bg-gray-700'
  if (count <= 2) return 'bg-green-200 dark:bg-green-800'
  if (count <= 5) return 'bg-green-400 dark:bg-green-600'
  if (count <= 10) return 'bg-green-500 dark:bg-green-500'
  return 'bg-green-700 dark:bg-green-400'
}

/* ------------------------------------------------------------------ */
/*  Component                                                         */
/* ------------------------------------------------------------------ */

export default function Profile() {
  const { user, loadUser } = useAuthStore()

  const [stats, setStats] = useState<UserStats | null>(null)
  const [calendar, setCalendar] = useState<ActivityCalendarResponse | null>(null)
  const [variants, setVariants] = useState<SavedVariant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [displayName, setDisplayName] = useState('')
  const [examDate, setExamDate] = useState('')
  const [targetScore, setTargetScore] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api<UserStats>('/api/users/me/stats'),
      api<ActivityCalendarResponse>('/api/progress/activity-calendar'),
      api<{ items: SavedVariant[] }>('/api/variants'),
    ])
      .then(([s, cal, v]) => {
        setStats(s)
        setCalendar(cal)
        setVariants(v.items)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  // Populate form from user profile
  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name ?? '')
      setExamDate(user.exam_date ?? '')
      setTargetScore(user.target_score != null ? String(user.target_score) : '')
    }
  }, [user])

  // Load full user profile (includes exam_date, target_score)
  useEffect(() => {
    loadUser()
  }, [loadUser])

  async function handleSave() {
    setSaving(true)
    setSaveMsg(null)
    setSaveError(null)

    const body: Record<string, unknown> = {}
    if (displayName.trim()) body.display_name = displayName.trim()
    if (examDate) body.exam_date = examDate
    if (targetScore) {
      const score = Number(targetScore)
      if (score < 27 || score > 100) {
        setSaveError('Целевой балл должен быть от 27 до 100')
        setSaving(false)
        return
      }
      body.target_score = score
    }

    try {
      await api('/api/users/me', {
        method: 'PATCH',
        body: JSON.stringify(body),
        headers: { 'Content-Type': 'application/json' },
      })
      await loadUser()
      // Refresh stats
      const s = await api<UserStats>('/api/users/me/stats')
      setStats(s)
      setSaveMsg('Сохранено')
      setTimeout(() => setSaveMsg(null), 3000)
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  /* ---- Loading / Error ---- */

  if (loading) {
    return (
      <div className="p-8">
        <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">Профиль</h1>
        <div className="space-y-6">
          <div className="h-48 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
          <div className="h-64 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
          <div className="h-40 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-800" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="mb-4 text-2xl font-bold text-gray-900 dark:text-gray-100">Профиль</h1>
        <p className="text-red-600">Ошибка загрузки: {error}</p>
      </div>
    )
  }

  const currentXp = stats?.current_xp ?? 0
  const currentLevel = stats?.current_level ?? 1
  const nextLevelXp = xpForNextLevel(currentXp)
  const currentLevelXp = xpForCurrentLevel(currentXp)
  const xpProgress = nextLevelXp
    ? ((currentXp - currentLevelXp) / (nextLevelXp - currentLevelXp)) * 100
    : 100

  const heatmapWeeks = calendar ? buildMiniHeatmap(calendar.activities) : []

  return (
    <div className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">Профиль</h1>

      {/* ====== Stats cards ====== */}
      <section className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="text-2xl font-bold text-blue-600">{ currentXp}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">XP</div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="text-2xl font-bold text-purple-600">
            {levelName(currentLevel)}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Уровень {currentLevel}</div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="text-2xl font-bold text-orange-600">{stats?.current_streak ?? 0}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Серия</div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <div className="text-2xl font-bold text-green-600">{stats?.longest_streak ?? 0}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Макс. серия</div>
        </div>
      </section>

      {/* XP progress to next level */}
      <section className="mb-8 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            Ур. {currentLevel} — {levelName(currentLevel)}
          </span>
          <span className="text-gray-500 dark:text-gray-400">
            {nextLevelXp ? `${currentXp} / ${nextLevelXp} XP` : 'Максимальный уровень'}
          </span>
        </div>
        <div className="h-3 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all"
            style={{ width: `${xpProgress}%` }}
          />
        </div>
        {nextLevelXp && (
          <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
            До уровня {currentLevel + 1} ({levelName(currentLevel + 1)}): ещё {nextLevelXp - currentXp} XP
          </p>
        )}
      </section>

      {/* ====== Settings form ====== */}
      <section className="mb-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">Настройки</h2>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Имя</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Ваше имя"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Дата экзамена</label>
            <input
              type="date"
              value={examDate}
              onChange={(e) => setExamDate(e.target.value)}
              min={new Date().toISOString().slice(0, 10)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Целевой балл (27–100)
            </label>
            <input
              type="number"
              min={27}
              max={100}
              value={targetScore}
              onChange={(e) => setTargetScore(e.target.value)}
              placeholder="80"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
            />
            {targetScore && (Number(targetScore) < 27 || Number(targetScore) > 100) && (
              <p className="mt-1 text-xs text-red-500">Допустимый диапазон: 27–100</p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
            {saveMsg && <span className="text-sm text-green-600">{saveMsg}</span>}
            {saveError && <span className="text-sm text-red-600">{saveError}</span>}
          </div>
        </div>
      </section>

      {/* ====== Streak heatmap (mini) ====== */}
      <section className="mb-8 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Календарь стриков</h2>
          {calendar && (
            <div className="flex gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span>Серия: <strong className="text-gray-900 dark:text-gray-100">{calendar.current_streak}</strong></span>
              <span>Макс: <strong className="text-gray-900 dark:text-gray-100">{calendar.longest_streak}</strong></span>
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          {['Пн', '', 'Ср', '', 'Пт', '', ''].map((dayLabel, dayIdx) => (
            <div key={dayIdx} className="flex items-center">
              <div className="w-6 shrink-0 text-[10px] text-gray-400 dark:text-gray-500">{dayLabel}</div>
              {heatmapWeeks.map((week, wi) => {
                const cell = week[dayIdx]
                if (!cell) return <div key={wi} style={{ width: 12, height: 12, margin: 1 }} />
                const isFuture = cell.date > new Date()
                return (
                  <div
                    key={wi}
                    title={`${cell.date.toISOString().slice(0, 10)}: ${cell.count} задач`}
                    className={`rounded-sm ${isFuture ? 'bg-transparent' : heatmapCellColor(cell.count)}`}
                    style={{ width: 10, height: 10, margin: 1 }}
                  />
                )
              })}
            </div>
          ))}

          {/* Legend */}
          <div className="mt-2 flex items-center justify-end gap-1 text-[10px] text-gray-400 dark:text-gray-500">
            <span>Меньше</span>
            <div className="h-2.5 w-2.5 rounded-sm bg-gray-100 dark:bg-gray-700" />
            <div className="h-2.5 w-2.5 rounded-sm bg-green-200 dark:bg-green-800" />
            <div className="h-2.5 w-2.5 rounded-sm bg-green-400 dark:bg-green-600" />
            <div className="h-2.5 w-2.5 rounded-sm bg-green-500" />
            <div className="h-2.5 w-2.5 rounded-sm bg-green-700 dark:bg-green-400" />
            <span>Больше</span>
          </div>
        </div>
      </section>

      {/* ====== Saved variants ====== */}
      {variants.length > 0 && (
        <section className="mb-8 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-gray-100">Сохранённые варианты</h2>
          <div className="space-y-2">
            {variants.map((v) => (
              <div key={v.id} className="flex items-center gap-3 rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/50">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
                  {v.task_number}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{v.name}</div>
                  <div className="text-xs text-gray-400 dark:text-gray-500">
                    {v.problem_count} задач &middot; {new Date(v.created_at).toLocaleDateString('ru-RU')}
                  </div>
                </div>
                <Link
                  to={`/print?task=${v.task_number}&count=${v.problem_count}&seed=${v.seed}`}
                  className="shrink-0 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700"
                >
                  Открыть
                </Link>
                <button
                  onClick={async () => {
                    await api(`/api/variants/${v.id}`, { method: 'DELETE' })
                    setVariants((prev) => prev.filter((x) => x.id !== v.id))
                  }}
                  className="shrink-0 rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20"
                >
                  Удалить
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ====== Score conversion table ====== */}
      <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-gray-100">Шкала перевода баллов</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-2 font-medium text-gray-600 dark:text-gray-400">Первичный балл</th>
                <th className="px-4 py-2 font-medium text-gray-600 dark:text-gray-400">Тестовый балл</th>
              </tr>
            </thead>
            <tbody>
              {SCORE_TABLE.map((row) => (
                <tr key={row.primary} className="border-b border-gray-100 dark:border-gray-700">
                  <td className="px-4 py-2 text-gray-900 dark:text-gray-100">{row.primary}</td>
                  <td className="px-4 py-2 text-gray-700 dark:text-gray-300">{row.score100}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
