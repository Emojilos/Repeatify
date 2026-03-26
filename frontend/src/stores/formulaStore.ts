import { create } from 'zustand'

interface FormulaState {
  isOpen: boolean
  activeTaskNumber: number | null
  open: () => void
  close: () => void
  toggle: () => void
  setActiveTask: (taskNumber: number | null) => void
}

export const useFormulaStore = create<FormulaState>((set) => ({
  isOpen: false,
  activeTaskNumber: null,
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  setActiveTask: (taskNumber) => set({ activeTaskNumber: taskNumber }),
}))
