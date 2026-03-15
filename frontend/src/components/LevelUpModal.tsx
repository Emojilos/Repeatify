import { useEffect } from 'react'
import { useXpStore } from '../stores/xpStore'

export default function LevelUpModal() {
  const level = useXpStore((s) => s.levelUpLevel)
  const name = useXpStore((s) => s.levelUpName)
  const dismiss = useXpStore((s) => s.dismissLevelUp)

  useEffect(() => {
    if (level === null) return
    const timer = setTimeout(dismiss, 4000)
    return () => clearTimeout(timer)
  }, [level, dismiss])

  if (level === null) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={dismiss}>
      <div
        className="animate-level-up rounded-2xl bg-white px-10 py-8 text-center shadow-2xl dark:bg-gray-800"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-2 text-4xl">&#127942;</div>
        <h2 className="mb-1 text-xl font-bold text-gray-900 dark:text-gray-100">Новый уровень!</h2>
        <p className="text-3xl font-extrabold text-purple-600">
          {level}. {name}
        </p>
        <button
          onClick={dismiss}
          className="mt-5 rounded-lg bg-purple-600 px-6 py-2 text-sm font-medium text-white hover:bg-purple-700"
        >
          Отлично!
        </button>
      </div>
    </div>
  )
}
