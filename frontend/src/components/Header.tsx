import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <Link to="/dashboard" className="text-xl font-bold text-blue-600">
        Repeatify
      </Link>

      <div className="flex items-center gap-6">
        {/* XP / Level / Streak stubs — will be wired to real data in TASK-011+ */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="rounded-full bg-blue-50 px-3 py-1 font-medium text-blue-700">
            0 XP
          </span>
          <span className="rounded-full bg-purple-50 px-3 py-1 font-medium text-purple-700">
            Ур. 1
          </span>
          <span className="rounded-full bg-orange-50 px-3 py-1 font-medium text-orange-700">
            🔥 0
          </span>
        </div>

        <button
          onClick={() => {
            localStorage.removeItem('access_token')
            window.location.hash = '#/auth/login'
          }}
          className="rounded-md px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700"
        >
          Выйти
        </button>
      </div>
    </header>
  )
}
