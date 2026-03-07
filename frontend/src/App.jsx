import { Routes, Route, Navigate } from 'react-router-dom'
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

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/onboarding" element={<PlaceholderPage title="Онбординг" />} />
      <Route path="/dashboard" element={<PlaceholderPage title="Dashboard" />} />
      <Route path="/train" element={<PlaceholderPage title="Тренировка" />} />
      <Route path="/topics" element={<PlaceholderPage title="Темы" />} />
      <Route path="/settings" element={<PlaceholderPage title="Настройки" />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
