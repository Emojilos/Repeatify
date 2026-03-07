import { supabase } from '../../config/supabase.js'

/**
 * Register a new user with email and password.
 * Supabase sends a confirmation email automatically.
 */
export async function signUp(email, password) {
  const { data, error } = await supabase.auth.signUp({ email, password })
  if (error) throw error
  return data
}

/**
 * Sign in an existing user with email and password.
 */
export async function signIn(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) throw error
  return data
}

/**
 * Sign out the current user and clear the Supabase session.
 */
export async function signOut() {
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

/**
 * Get the current session synchronously (may be null if not authenticated).
 */
export async function getSession() {
  const { data, error } = await supabase.auth.getSession()
  if (error) throw error
  return data.session
}

/**
 * Subscribe to auth state changes.
 * @param {function} callback - called with (event, session)
 * @returns {function} unsubscribe function
 */
export function onAuthStateChange(callback) {
  const { data: { subscription } } = supabase.auth.onAuthStateChange(callback)
  return () => subscription.unsubscribe()
}
