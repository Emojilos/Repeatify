import { NavLink } from 'react-router-dom'

type IconName = 'dashboard' | 'plan' | 'tasks' | 'practice' | 'progress' | 'profile'

const navItems: { to: string; label: string; icon: IconName }[] = [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/plan', label: 'Мой план', icon: 'plan' },
  { to: '/topics', label: 'Задания', icon: 'tasks' },
  { to: '/practice', label: 'Тренировка', icon: 'practice' },
  { to: '/progress', label: 'Прогресс', icon: 'progress' },
  { to: '/profile', label: 'Профиль', icon: 'profile' },
]

function SidebarIcon({ name }: { name: IconName }) {
  const common = {
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    strokeWidth: 1.8,
  }

  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5 shrink-0">
      {name === 'dashboard' && (
        <>
          <path {...common} d="M4 13.5h6.5V20H4z" />
          <path {...common} d="M13.5 4H20v16h-6.5z" />
          <path {...common} d="M4 4h6.5v6.5H4z" />
        </>
      )}
      {name === 'plan' && (
        <>
          <path {...common} d="M5 5.5h14v14H5z" />
          <path {...common} d="M8 3.5v4" />
          <path {...common} d="M16 3.5v4" />
          <path {...common} d="M5 9.5h14" />
        </>
      )}
      {name === 'tasks' && (
        <>
          <path {...common} d="M5 5h14v14H5z" />
          <path {...common} d="M8 9h8" />
          <path {...common} d="M8 13h8" />
          <path {...common} d="M8 17h4" />
        </>
      )}
      {name === 'practice' && (
        <>
          <circle {...common} cx="12" cy="12" r="7" />
          <circle {...common} cx="12" cy="12" r="3" />
          <path {...common} d="M12 5V3" />
          <path {...common} d="M19 12h2" />
        </>
      )}
      {name === 'progress' && (
        <>
          <path {...common} d="M4 19h16" />
          <path {...common} d="M6 16l4-5 3 3 5-8" />
        </>
      )}
      {name === 'profile' && (
        <>
          <circle {...common} cx="12" cy="8" r="3.5" />
          <path {...common} d="M5 20c1.2-3.5 3.6-5 7-5s5.8 1.5 7 5" />
        </>
      )}
    </svg>
  )
}

export default function Sidebar() {
  return (
    <aside className="flex w-56 flex-col border-r border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-100'
              }`
            }
          >
            <SidebarIcon name={item.icon} />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
