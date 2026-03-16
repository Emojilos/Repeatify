import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '\u{1F4CA}' },
  { to: '/plan', label: '\u041C\u043E\u0439 \u043F\u043B\u0430\u043D', icon: '\u{1F4C5}' },
  { to: '/topics', label: '\u0422\u0435\u043C\u044B', icon: '\u{1F4DA}' },
  { to: '/practice', label: '\u0422\u0440\u0435\u043D\u0438\u0440\u043E\u0432\u043A\u0430', icon: '\u{1F3AF}' },
  { to: '/progress', label: '\u041F\u0440\u043E\u0433\u0440\u0435\u0441\u0441', icon: '\u{1F4C8}' },
  { to: '/profile', label: '\u041F\u0440\u043E\u0444\u0438\u043B\u044C', icon: '\u{1F464}' },
]

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
            <span className="text-base">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
