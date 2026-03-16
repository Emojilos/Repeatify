import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

/**
 * Redirects authenticated users who haven't completed onboarding/diagnostic.
 * - No target_score → /onboarding
 * - No diagnostic → /diagnostic
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

  // Onboarding done but no diagnostic
  if (user.target_score && !user.has_diagnostic) {
    if (location.pathname !== '/diagnostic') {
      return <Navigate to="/diagnostic" replace />
    }
  }

  return <Outlet />
}
