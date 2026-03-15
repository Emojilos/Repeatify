import { create } from 'zustand'

interface XpNotification {
  id: number
  amount: number
}

interface XpState {
  notifications: XpNotification[]
  levelUpLevel: number | null
  levelUpName: string | null

  notifyXp: (amount: number) => void
  removeNotification: (id: number) => void
  showLevelUp: (level: number, name: string) => void
  dismissLevelUp: () => void
}

let nextId = 0

/* Level table matching backend xp_service.py */
const LEVEL_TABLE: [number, number, string][] = [
  [0, 1, 'Новичок'],
  [100, 2, 'Ученик'],
  [300, 3, 'Практикант'],
  [600, 4, 'Решатель'],
  [1000, 5, 'Знаток'],
  [1500, 6, 'Эксперт'],
  [2500, 7, 'Мастер'],
  [4000, 8, 'Гуру'],
  [6000, 9, 'Легенда'],
  [10000, 10, 'Бог ЕГЭ'],
]

export function levelName(level: number): string {
  const entry = LEVEL_TABLE.find(([, num]) => num === level)
  return entry ? entry[2] : 'Новичок'
}

export function xpForNextLevel(currentXp: number): number | null {
  for (const [minXp] of LEVEL_TABLE) {
    if (currentXp < minXp) return minXp
  }
  return null
}

export function xpForCurrentLevel(currentXp: number): number {
  let prev = 0
  for (const [minXp] of LEVEL_TABLE) {
    if (currentXp < minXp) return prev
    prev = minXp
  }
  return prev
}

export const useXpStore = create<XpState>((set) => ({
  notifications: [],
  levelUpLevel: null,
  levelUpName: null,

  notifyXp: (amount: number) => {
    if (amount <= 0) return
    const id = ++nextId
    set((state) => ({
      notifications: [...state.notifications, { id, amount }],
    }))
  },

  removeNotification: (id: number) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }))
  },

  showLevelUp: (level: number, name: string) => {
    set({ levelUpLevel: level, levelUpName: name })
  },

  dismissLevelUp: () => {
    set({ levelUpLevel: null, levelUpName: null })
  },
}))
