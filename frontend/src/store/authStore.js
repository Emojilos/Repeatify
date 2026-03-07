import { create } from 'zustand'
import { getSession, onAuthStateChange, signOut } from '../services/supabase/auth.service.js'

const useAuthStore = create((set) => ({
  user: null,
  session: null,
  isLoading: true,

  initialize: async () => {
    try {
      const session = await getSession()
      set({ session, user: session?.user ?? null, isLoading: false })
    } catch {
      set({ session: null, user: null, isLoading: false })
    }

    const unsubscribe = onAuthStateChange((_event, session) => {
      set({ session, user: session?.user ?? null, isLoading: false })
    })

    return unsubscribe
  },

  logout: async () => {
    await signOut()
    set({ session: null, user: null })
  },
}))

export default useAuthStore
