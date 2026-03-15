import { create } from 'zustand'
import { api } from '../lib/api'

export interface SRSCard {
  card_id: string
  problem_id: string
  topic_id: string
  topic_title: string | null
  task_number: number
  card_type: string
  problem_text: string
  problem_images: string[] | null
  hints: string[] | null
  difficulty: string | null
  ease_factor: number
  interval_days: number
  repetition_count: number
}

interface SRSSessionResponse {
  cards: SRSCard[]
  total_due: number
}

export interface ReviewResult {
  is_correct: boolean
  correct_answer: string | null
  solution_markdown: string | null
  xp_earned: number
  next_review_date: string
  new_interval: number
  new_ease_factor: number
  new_level_reached: number | null
}

export interface CardResult {
  card: SRSCard
  review: ReviewResult
  assessment: string
}

interface SessionState {
  cards: SRSCard[]
  totalDue: number
  currentIndex: number
  results: CardResult[]
  loading: boolean
  error: string | null

  fetchSession: (maxCards?: number) => Promise<void>
  submitReview: (cardId: string, answer: string, timeSpent: number, assessment: string) => Promise<ReviewResult | null>
  advanceCard: () => void
  addResult: (result: CardResult) => void
  reset: () => void
  isFinished: () => boolean
}

export const useSessionStore = create<SessionState>((set, get) => ({
  cards: [],
  totalDue: 0,
  currentIndex: 0,
  results: [],
  loading: false,
  error: null,

  fetchSession: async (maxCards = 20) => {
    set({ loading: true, error: null })
    try {
      const res = await api<SRSSessionResponse>(`/api/srs/session?max_cards=${maxCards}`)
      set({ cards: res.cards, totalDue: res.total_due, currentIndex: 0, results: [], loading: false })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Ошибка загрузки сессии', loading: false })
    }
  },

  submitReview: async (cardId, answer, timeSpent, assessment) => {
    try {
      const res = await api<ReviewResult>('/api/srs/review', {
        method: 'POST',
        body: JSON.stringify({
          card_id: cardId,
          answer,
          time_spent_seconds: timeSpent,
          self_assessment: assessment,
        }),
      })
      return res
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Ошибка отправки' })
      return null
    }
  },

  advanceCard: () => {
    set((state) => ({ currentIndex: state.currentIndex + 1 }))
  },

  addResult: (result) => {
    set((state) => ({ results: [...state.results, result] }))
  },

  reset: () => {
    set({ cards: [], totalDue: 0, currentIndex: 0, results: [], loading: false, error: null })
  },

  isFinished: () => {
    const { currentIndex, cards } = get()
    return cards.length > 0 && currentIndex >= cards.length
  },
}))
