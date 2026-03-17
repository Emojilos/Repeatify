import { create } from 'zustand'
import { api } from '../lib/api'

export interface FSRSCard {
  id: string
  user_id: string
  problem_id: string | null
  prototype_id: string | null
  card_type: string
  difficulty: number
  stability: number
  due: string
  last_review: string | null
  reps: number
  lapses: number
  state: string
  scheduled_days: number | null
  elapsed_days: number | null
  created_at: string | null
  // Enriched fields for session display
  problem_text: string | null
  problem_images: string[] | null
  hints: string[] | null
  topic_title: string | null
  task_number: number | null
  retrievability: number | null
}

interface FSRSSessionResponse {
  cards: FSRSCard[]
  total_due: number
}

export interface ReviewResult {
  is_correct: boolean
  correct_answer: string | null
  solution_markdown: string | null
  xp_earned: number
  new_level_reached: number | null
  // FSRS-specific fields
  new_due: string
  new_difficulty: number
  new_stability: number
  new_state: string
  retrievability: number | null
}

export interface CardResult {
  card: FSRSCard
  review: ReviewResult
  assessment: string
}

interface SessionState {
  cards: FSRSCard[]
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

const ASSESSMENT_TO_RATING: Record<string, number> = {
  again: 1,
  hard: 2,
  good: 3,
  easy: 4,
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
      const res = await api<FSRSSessionResponse>(`/api/fsrs/session?max_cards=${maxCards}`)
      set({ cards: res.cards, totalDue: res.total_due, currentIndex: 0, results: [], loading: false })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Ошибка загрузки сессии', loading: false })
    }
  },

  submitReview: async (cardId, answer, timeSpent, assessment) => {
    try {
      const rating = ASSESSMENT_TO_RATING[assessment] ?? 3
      const res = await api<ReviewResult>('/api/fsrs/review', {
        method: 'POST',
        body: JSON.stringify({
          card_id: cardId,
          rating,
          answer,
          time_spent_seconds: timeSpent,
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
