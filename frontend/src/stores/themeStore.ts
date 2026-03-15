import { create } from 'zustand'

type Theme = 'light' | 'dark'

interface ThemeState {
  theme: Theme
  toggle: () => void
}

function getInitialTheme(): Theme {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('repeatify-theme')
    if (stored === 'dark' || stored === 'light') return stored
  }
  return 'light'
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

export const useThemeStore = create<ThemeState>((set) => {
  const initial = getInitialTheme()
  applyTheme(initial)

  return {
    theme: initial,
    toggle: () =>
      set((state) => {
        const next: Theme = state.theme === 'light' ? 'dark' : 'light'
        localStorage.setItem('repeatify-theme', next)
        applyTheme(next)
        return { theme: next }
      }),
  }
})
