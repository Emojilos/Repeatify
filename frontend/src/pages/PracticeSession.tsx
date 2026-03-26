import { useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useSessionStore } from '../stores/sessionStore'
import type { FSRSCard, ReviewResult } from '../stores/sessionStore'
import ProblemCard from '../components/ProblemCard'
import { useFormulaStore } from '../stores/formulaStore'

interface Problem {
  id: string
  topic_id: string
  task_number: number
  difficulty: string
  problem_text: string
  problem_images?: string[] | null
  hints?: string[] | null
  source?: string | null
  prototype_id?: string | null
  prototype_code?: string | null
  prototype_title?: string | null
}

function fsrsCardToProblem(card: FSRSCard): Problem {
  return {
    id: card.problem_id || card.id,
    topic_id: '',
    task_number: card.task_number || 0,
    difficulty: 'medium',
    problem_text: card.problem_text || '',
    problem_images: card.problem_images,
    hints: card.hints,
    prototype_id: card.prototype_id,
    prototype_code: card.prototype_code,
    prototype_title: card.prototype_title,
  }
}

export default function PracticeSession() {
  const navigate = useNavigate()
  const {
    cards,
    currentIndex,
    results,
    loading,
    error,
    fetchSession,
    submitReview,
    advanceCard,
    addResult,
    isFinished,
  } = useSessionStore()

  const setActiveTask = useFormulaStore((s) => s.setActiveTask)

  useEffect(() => {
    if (cards.length === 0 && !loading) {
      fetchSession()
    }
  }, [cards.length, loading, fetchSession])

  useEffect(() => {
    if (isFinished()) {
      navigate('/practice/results')
    }
  }, [currentIndex, cards.length, isFinished, navigate])

  const currentCard = cards[currentIndex]

  // Set active task for formula sheet
  useEffect(() => {
    if (currentCard?.task_number) setActiveTask(currentCard.task_number)
    return () => setActiveTask(null)
  }, [currentCard?.task_number, setActiveTask])

  const handleSubmitOverride = useCallback(
    async (answer: string, timeSpent: number, assessment: string) => {
      if (!currentCard) return null
      const review = await submitReview(currentCard.id, answer, timeSpent, assessment)
      if (!review) return null
      return {
        is_correct: review.is_correct,
        correct_answer: review.correct_answer || '',
        solution_markdown: review.solution_markdown,
        xp_earned: review.xp_earned,
        attempt_id: currentCard.id,
        new_level_reached: review.new_level_reached,
      }
    },
    [currentCard, submitReview],
  )

  const handleComplete = useCallback(
    (assessment: string, result: { is_correct: boolean; xp_earned: number; correct_answer: string; solution_markdown: string | null }) => {
      if (!currentCard) return

      const reviewResult: ReviewResult = {
        is_correct: result.is_correct,
        correct_answer: result.correct_answer,
        solution_markdown: result.solution_markdown,
        xp_earned: result.xp_earned,
        new_level_reached: null,
        new_due: '',
        new_difficulty: currentCard.difficulty,
        new_stability: currentCard.stability,
        new_state: currentCard.state,
        retrievability: currentCard.retrievability,
      }

      addResult({ card: currentCard, review: reviewResult, assessment })

      setTimeout(() => {
        advanceCard()
      }, 1000)
    },
    [currentCard, addResult, advanceCard],
  )

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-6 h-8 w-64 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-64 animate-pulse rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <Link to="/practice" className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline">
          &larr; Назад
        </Link>
        <p className="mt-4 text-red-600">Ошибка: {error}</p>
      </div>
    )
  }

  if (cards.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="mb-2 text-5xl">🎉</div>
        <p className="mb-4 text-lg text-gray-500 dark:text-gray-400">Нет карточек на повторение</p>
        <Link
          to="/practice"
          className="inline-block rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
        >
          Назад
        </Link>
      </div>
    )
  }

  if (!currentCard) return null

  const completed = results.length
  const problem = fsrsCardToProblem(currentCard)

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <Link to="/practice" className="inline-flex items-center text-sm text-blue-600 hover:underline">
          &larr; Назад к тренировке
        </Link>
        <div className="flex items-center gap-3">
          {currentCard.retrievability != null && (
            <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-700 dark:bg-purple-900/40 dark:text-purple-300">
              {Math.round(currentCard.retrievability * 100)}% запоминание
            </span>
          )}
          {currentCard.topic_title && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {currentCard.topic_title}
            </span>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="mb-1.5 flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            Карточка {currentIndex + 1} из {cards.length}
          </span>
          <span className="text-gray-400 dark:text-gray-500">
            {completed} решено
            {results.reduce((sum, r) => sum + r.review.xp_earned, 0) > 0 &&
              ` \u2022 +${results.reduce((sum, r) => sum + r.review.xp_earned, 0)} XP`}
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-300"
            style={{ width: `${(completed / cards.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Current card */}
      <ProblemCard
        key={currentCard.id}
        problem={problem}
        onComplete={handleComplete}
        onSubmitOverride={handleSubmitOverride}
        showTimer
      />
    </div>
  )
}
