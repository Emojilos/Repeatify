import { create } from 'zustand'
import { apiPost } from '../services/api/client.js'

const useSessionStore = create((set, get) => ({
  // Session data
  sessionId: null,
  cards: [],
  currentIndex: 0,
  totalCards: 0,

  // Card state
  hintsUsed: 0,
  answerRevealed: false,
  startTime: null,

  // Session state: 'idle' | 'loading' | 'show_question' | 'show_answer' | 'rating' | 'submitting' | 'session_complete' | 'error'
  phase: 'idle',
  error: null,

  // Session results
  results: [],

  currentCard: () => {
    const { cards, currentIndex } = get()
    return cards[currentIndex] ?? null
  },

  loadSession: async (topicId) => {
    set({ phase: 'loading', error: null })
    try {
      const query = topicId ? `?topic_id=${topicId}` : ''
      const data = await apiPost(`/api/v1/session/generate${query}`)
      if (!data.cards || data.cards.length === 0) {
        set({ phase: 'session_complete', cards: [], results: [], totalCards: 0 })
        return
      }
      set({
        sessionId: data.session_id,
        cards: data.cards,
        totalCards: data.total_cards,
        currentIndex: 0,
        hintsUsed: 0,
        answerRevealed: false,
        startTime: Date.now(),
        phase: 'show_question',
        results: [],
        error: null,
      })
    } catch (err) {
      set({ phase: 'error', error: err.message })
    }
  },

  revealAnswer: () => {
    set({ answerRevealed: true, phase: 'show_answer' })
  },

  setHintsUsed: (count) => {
    set({ hintsUsed: count })
  },

  submitRating: async (rating) => {
    const { sessionId, cards, currentIndex, hintsUsed, startTime } = get()
    const card = cards[currentIndex]
    if (!card) return

    const responseTimeMs = Date.now() - (startTime || Date.now())
    set({ phase: 'submitting' })

    try {
      const result = await apiPost('/api/v1/session/review', {
        card_id: card.id,
        session_id: sessionId,
        rating,
        hints_used: hintsUsed,
        response_time_ms: responseTimeMs,
      })

      const newResults = [...get().results, { cardId: card.id, rating, ...result }]
      const nextIndex = currentIndex + 1

      if (nextIndex >= cards.length) {
        set({ results: newResults, phase: 'session_complete' })
      } else {
        set({
          results: newResults,
          currentIndex: nextIndex,
          hintsUsed: 0,
          answerRevealed: false,
          startTime: Date.now(),
          phase: 'show_question',
        })
      }
    } catch (err) {
      // On error, stay on current card and let user retry
      set({ phase: 'show_answer', error: err.message })
    }
  },

  reset: () => {
    set({
      sessionId: null,
      cards: [],
      currentIndex: 0,
      totalCards: 0,
      hintsUsed: 0,
      answerRevealed: false,
      startTime: null,
      phase: 'idle',
      error: null,
      results: [],
    })
  },
}))

export default useSessionStore
