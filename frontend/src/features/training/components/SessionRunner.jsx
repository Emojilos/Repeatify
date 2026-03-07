import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useSessionStore from '../../../store/sessionStore.js'
import CardQuestion from './CardQuestion.jsx'
import RatingButtons from './RatingButtons.jsx'
import StepByStepReveal from './StepByStepReveal.jsx'
import SessionProgressBar from './SessionProgressBar.jsx'
import LatexRenderer from '../../../components/math/LatexRenderer.jsx'

export default function SessionRunner() {
  const navigate = useNavigate()
  const {
    cards,
    currentIndex,
    totalCards,
    hintsUsed,
    answerRevealed,
    phase,
    error,
    results,
    loadSession,
    revealAnswer,
    setHintsUsed,
    submitRating,
    reset,
  } = useSessionStore()

  const card = cards[currentIndex] ?? null

  useEffect(() => {
    loadSession()
    return () => reset()
  }, [loadSession, reset])

  // Loading state
  if (phase === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-gray-500">Загружаем сессию...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (phase === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md px-4">
          <p className="text-red-600 font-medium mb-4">{error}</p>
          <button
            onClick={() => loadSession()}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors cursor-pointer"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    )
  }

  // Session complete
  if (phase === 'session_complete') {
    const total = results.length
    const correct = results.filter(r => r.rating >= 3).length
    const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md px-4">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Сессия завершена!</h2>

          {total === 0 ? (
            <p className="text-gray-500 mb-6">Нет карточек для повторения. Отличная работа!</p>
          ) : (
            <>
              <p className="text-gray-600 mb-6">
                {correct} из {total} — точность {accuracy}%
              </p>

              <p className="text-gray-500 text-sm mb-8">
                {accuracy >= 80
                  ? 'Отличный результат! Так держать!'
                  : accuracy >= 50
                    ? 'Хороший прогресс! С каждым разом будет лучше.'
                    : 'Каждая тренировка делает тебя сильнее. Продолжай!'}
              </p>
            </>
          )}

          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors cursor-pointer"
            >
              На главную
            </button>
            <button
              onClick={() => loadSession()}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors cursor-pointer"
            >
              Ещё сессия
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Active session — show_question / show_answer / rating / submitting
  if (!card) return null

  const isStepByStep = card.card_type === 'step_by_step'
  const maxRating = hintsUsed >= (card.solution_steps?.length || 0) && isStepByStep ? 2 : hintsUsed > 0 ? 2 : 4
  const showRating = answerRevealed
  const isSubmitting = phase === 'submitting'

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <SessionProgressBar current={currentIndex + 1} total={totalCards} />

        {/* Question */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-4">
          <CardQuestion card={card} />
        </div>

        {/* Step-by-step reveal for step_by_step cards */}
        {isStepByStep && answerRevealed && card.solution_steps && (
          <StepByStepReveal
            steps={card.solution_steps}
            onHintsUsedChange={setHintsUsed}
          />
        )}

        {/* Answer for basic_qa cards */}
        {!isStepByStep && answerRevealed && card.answer_text && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Ответ</h3>
            <div className="text-[16px] leading-relaxed text-gray-800">
              <LatexRenderer text={card.answer_text} />
            </div>
          </div>
        )}

        {/* Show answer button */}
        {!answerRevealed && (
          <button
            onClick={revealAnswer}
            className="w-full max-w-2xl mx-auto block py-4 rounded-lg bg-gray-800 text-white font-medium
                       hover:bg-gray-900 transition-colors cursor-pointer"
          >
            Показать ответ
          </button>
        )}

        {/* Rating buttons */}
        {showRating && (
          <div className="mt-4">
            {error && (
              <p className="text-red-500 text-sm text-center mb-2">{error}</p>
            )}
            <RatingButtons
              onRate={submitRating}
              disabled={isSubmitting}
              maxRating={maxRating}
            />
          </div>
        )}
      </div>
    </div>
  )
}
