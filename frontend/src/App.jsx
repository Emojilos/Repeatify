import { Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './store/authStore.js'
import PrivateRoute from './components/auth/PrivateRoute.jsx'
import LoginPage from './features/auth/LoginPage.jsx'
import RegisterPage from './features/auth/RegisterPage.jsx'

function PlaceholderPage({ title }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-800">{title}</h1>
        <p className="mt-2 text-gray-500">Страница в разработке</p>
      </div>
    </div>
  )
}

function AuthRedirect({ children }) {
  const { session, isLoading } = useAuthStore()
  if (isLoading) return null
  if (session) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      {/* Public routes — redirect to /dashboard if already authenticated */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/login"
        element={<AuthRedirect><LoginPage /></AuthRedirect>}
      />
      <Route
        path="/register"
        element={<AuthRedirect><RegisterPage /></AuthRedirect>}
      />

      {/* Protected routes */}
      <Route element={<PrivateRoute />}>
        <Route path="/onboarding" element={<PlaceholderPage title="Онбординг" />} />
        <Route path="/dashboard" element={<PlaceholderPage title="Dashboard" />} />
        <Route path="/train" element={<PlaceholderPage title="Тренировка" />} />
        <Route path="/topics" element={<PlaceholderPage title="Темы" />} />
        <Route path="/settings" element={<PlaceholderPage title="Настройки" />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
