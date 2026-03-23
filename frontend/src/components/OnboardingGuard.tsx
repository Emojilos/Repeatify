import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

/**
 * Redirects authenticated users who haven't completed onboarding.
 * - No target_score → /onboarding
 * - Otherwise → render children (Layout)
 */
export default function OnboardingGuard() {
  const { user } = useAuthStore()
  const location = useLocation()

  // Wait until user data is loaded
  if (!user) {
    return <Outlet />
  }

  // No target_score means onboarding not completed
  if (!user.target_score) {
    if (location.pathname !== '/onboarding') {
      return <Navigate to="/onboarding" replace />
    }
  }

  return <Outlet />
}
