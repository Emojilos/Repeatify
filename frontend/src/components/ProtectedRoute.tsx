import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export default function ProtectedRoute() {
  const { isAuthenticated, user, loadUser } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated && !user) {
      loadUser()
    }
  }, [isAuthenticated, user, loadUser])

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />
  }

  return <Outlet />
}
