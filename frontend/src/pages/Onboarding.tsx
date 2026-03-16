import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const TARGET_OPTIONS: { value: number; label: string; description: string }[] = [
  { value: 70, label: '70 баллов', description: 'Идеальная Часть 1' },
  { value: 80, label: '80 баллов', description: 'Джентльменский набор' },
  { value: 90, label: '90 баллов', description: '+ Геометрия и параметры' },
  { value: 100, label: '100 баллов', description: 'Максимум' },
]

const HOURS_OPTIONS = [0.5, 1, 1.5, 2, 3]

/* Default exam date: ЕГЭ-2026 (usually late May / early June) */
const DEFAULT_EXAM_DATE = '2026-05-28'

const STEP_LABELS = ['Цель', 'Время', 'Дата экзамена']

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function Onboarding() {
  const navigate = useNavigate()
  const loadUser = useAuthStore((s) => s.loadUser)

  const [step, setStep] = useState(0)
  const [targetScore, setTargetScore] = useState<number | null>(null)
  const [hoursPerDay, setHoursPerDay] = useState<number | null>(null)
  const [examDate, setExamDate] = useState(DEFAULT_EXAM_DATE)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canNext =
    (step === 0 && targetScore !== null) ||
    (step === 1 && hoursPerDay !== null) ||
    step === 2

  async function handleFinish() {
    setSaving(true)
    setError(null)
    try {
      await api('/api/users/me', {
        method: 'PATCH',
        body: JSON.stringify({
          target_score: targetScore,
          hours_per_day: hoursPerDay,
          exam_date: examDate,
        }),
      })
      await loadUser()
      navigate('/diagnostic')
    } catch {
      setError('Не удалось сохранить настройки. Попробуйте ещё раз.')
    } finally {
      setSaving(false)
    }
  }

  function handleNext() {
    if (step < 2) {
      setStep(step + 1)
    } else {
      handleFinish()
    }
  }

  function handleBack() {
    if (step > 0) setStep(step - 1)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Добро пожаловать в Repeatify
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Настроим подготовку под вас
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {STEP_LABELS.map((label, i) => (
            <div key={label} className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (i < step) setStep(i)
                }}
                disabled={i > step}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                  i === step
                    ? 'bg-blue-600 text-white'
                    : i < step
                      ? 'bg-green-500 text-white cursor-pointer'
                      : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400'
                }`}
              >
                {i < step ? '\u2713' : i + 1}
              </button>
              <span
                className={`text-sm hidden sm:inline ${
                  i === step
                    ? 'text-blue-600 dark:text-blue-400 font-medium'
                    : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                {label}
              </span>
              {i < STEP_LABELS.length - 1 && (
                <div
                  className={`w-8 h-0.5 ${
                    i < step ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 sm:p-8">
          {/* Step 1: Target score */}
          {step === 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Какой балл вы хотите получить?
              </h2>
              <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
                Мы составим план, чтобы достичь вашей цели
              </p>
              <div className="grid grid-cols-1 gap-3">
                {TARGET_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setTargetScore(opt.value)}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      targetScore === opt.value
                        ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/30 dark:border-blue-500'
                        : 'border-gray-200 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-700'
                    }`}
                  >
                    <span className="text-lg font-semibold text-gray-900 dark:text-white">
                      {opt.label}
                    </span>
                    <span className="block text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                      {opt.description}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Hours per day */}
          {step === 1 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Сколько часов в день готовы заниматься?
              </h2>
              <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
                Учитывайте реальное свободное время
              </p>
              <div className="grid grid-cols-5 gap-2 sm:gap-3">
                {HOURS_OPTIONS.map((h) => (
                  <button
                    key={h}
                    onClick={() => setHoursPerDay(h)}
                    className={`py-4 rounded-xl border-2 text-center transition-all ${
                      hoursPerDay === h
                        ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/30 dark:border-blue-500'
                        : 'border-gray-200 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-700'
                    }`}
                  >
                    <span className="text-lg font-semibold text-gray-900 dark:text-white">
                      {h}
                    </span>
                    <span className="block text-xs text-gray-500 dark:text-gray-400 mt-1">
                      ч/день
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: Exam date */}
          {step === 2 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Когда экзамен?
              </h2>
              <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
                Дата ЕГЭ-2026 уже установлена, но вы можете изменить
              </p>
              <input
                type="date"
                value={examDate}
                min={new Date().toISOString().split('T')[0]}
                onChange={(e) => setExamDate(e.target.value)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white bg-white dark:bg-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
              {examDate && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
                  До экзамена:{' '}
                  <span className="font-semibold text-blue-600 dark:text-blue-400">
                    {Math.max(
                      0,
                      Math.ceil(
                        (new Date(examDate).getTime() - Date.now()) /
                          (1000 * 60 * 60 * 24),
                      ),
                    )}{' '}
                    дней
                  </span>
                </p>
              )}
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
              disabled={step === 0}
              className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                step === 0
                  ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              Назад
            </button>
            <button
              onClick={handleNext}
              disabled={!canNext || saving}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saving
                ? 'Сохранение...'
                : step === 2
                  ? 'Начать диагностику'
                  : 'Далее'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
