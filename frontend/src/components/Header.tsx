import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { xpForNextLevel, xpForCurrentLevel } from '../stores/xpStore'
import { useThemeStore } from '../stores/themeStore'

export default function Header() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { theme, toggle } = useThemeStore()

  async function handleLogout() {
    await logout()
    navigate('/auth/login', { replace: true })
  }

  const currentXp = user?.current_xp ?? 0
  const nextXp = xpForNextLevel(currentXp)
  const currentLevelXp = xpForCurrentLevel(currentXp)
  const progress = nextXp
    ? ((currentXp - currentLevelXp) / (nextXp - currentLevelXp)) * 100
    : 100

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 dark:border-gray-700 dark:bg-gray-800">
      <Link to="/dashboard" className="text-xl font-bold text-blue-600">
        Repeatify
      </Link>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
          {/* XP with mini progress bar */}
          <div className="flex flex-col items-center gap-0.5">
            <span className="rounded-full bg-blue-50 px-3 py-1 font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
              {currentXp} XP
            </span>
            <div className="h-1 w-14 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
          <span className="rounded-full bg-purple-50 px-3 py-1 font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
            Ур. {user?.current_level ?? 1}
          </span>
          <span className="rounded-full bg-orange-50 px-3 py-1 font-medium text-orange-700 dark:bg-orange-900/30 dark:text-orange-300">
            {user?.current_streak ?? 0}
          </span>
        </div>

        {/* Theme toggle */}
        <button
          onClick={toggle}
          className="rounded-md p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300"
          title={theme === 'light' ? 'Тёмная тема' : 'Светлая тема'}
        >
          {theme === 'light' ? (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path fillRule="evenodd" d="M7.455 2.004a.75.75 0 0 1 .26.77 7 7 0 0 0 9.958 7.967.75.75 0 0 1 1.067.853A8.5 8.5 0 1 1 6.647 1.921a.75.75 0 0 1 .808.083Z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path d="M10 2a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 10 2ZM10 15a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 10 15ZM10 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6ZM15.657 5.404a.75.75 0 1 0-1.06-1.06l-1.061 1.06a.75.75 0 0 0 1.06 1.06l1.061-1.06ZM6.464 14.596a.75.75 0 1 0-1.06-1.06l-1.06 1.06a.75.75 0 0 0 1.06 1.06l1.06-1.06ZM18 10a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 18 10ZM5 10a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 5 10ZM14.596 15.657a.75.75 0 0 0 1.06-1.06l-1.06-1.061a.75.75 0 1 0-1.06 1.06l1.06 1.061ZM5.404 6.464a.75.75 0 0 0 1.06-1.06l-1.06-1.06a.75.75 0 1 0-1.06 1.06l1.06 1.06Z" />
            </svg>
          )}
        </button>

        <button
          onClick={handleLogout}
          className="rounded-md px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300"
        >
          Выйти
        </button>
      </div>
    </header>
  )
}
