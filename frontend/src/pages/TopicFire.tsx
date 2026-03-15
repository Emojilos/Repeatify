import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import MathRenderer from '../components/MathRenderer'
import { useXpStore, levelName as getLevelName } from '../stores/xpStore'
import { useAuthStore } from '../stores/authStore'

interface TheoryContentItem {
  id: string
  topic_id: string
  content_type: string
  content_markdown: string
  visual_assets: unknown[]
  order_index: number
}

interface FireProgress {
  fire_framework_completed: boolean
  fire_inquiry_completed: boolean
  fire_relationships_completed: boolean
  fire_elaboration_completed: boolean
  fire_completed_at: string | null
}

interface TheoryResponse {
  topic_id: string
  topic_title: string
  items: TheoryContentItem[]
  fire_progress: FireProgress | null
}

interface FireProgressResponse {
  stage: string
  completed: boolean
  fire_completed_at: string | null
  all_stages_completed: boolean
  xp_earned: number
  new_level_reached: number | null
}

interface TopicRelationship {
  id: string
  source_topic_id: string
  target_topic_id: string
  relationship_type: string
  description: string | null
  related_topic: {
    id: string
    task_number: number
    title: string
  } | null
}

const STAGES = ['framework', 'inquiry', 'relationships', 'elaboration'] as const
type Stage = typeof STAGES[number]

const STAGE_LABELS: Record<Stage, string> = {
  framework: 'Каркас темы',
  inquiry: 'Исследование',
  relationships: 'Связи',
  elaboration: 'Объяснение',
}

const STAGE_SHORT: Record<Stage, string> = {
  framework: 'F',
  inquiry: 'I',
  relationships: 'R',
  elaboration: 'E',
}

const STAGE_DESCRIPTIONS: Record<Stage, string> = {
  framework: 'Изучите ключевые концепции и формулы темы',
  inquiry: 'Ответьте на исследовательские вопросы для глубокого понимания',
  relationships: 'Изучите связи этой темы с другими заданиями ЕГЭ',
  elaboration: 'Объясните тему своими словами и проверьте понимание',
}

function isStageCompleted(progress: FireProgress | null, stage: Stage): boolean {
  if (!progress) return false
  const key = `fire_${stage}_completed` as keyof FireProgress
  return progress[key] === true
}

export default function TopicFire() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [theory, setTheory] = useState<TheoryResponse | null>(null)
  const [relationships, setRelationships] = useState<TopicRelationship[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentStageIdx, setCurrentStageIdx] = useState(0)
  const [saving, setSaving] = useState(false)
  const [completed, setCompleted] = useState(false)
  const [xpEarned, setXpEarned] = useState(0)
  const [newLevel, setNewLevel] = useState<number | null>(null)

  // Inquiry answers (local state, not persisted)
  const [inquiryAnswers, setInquiryAnswers] = useState<Record<number, string>>({})
  const [showInquiryAnswers, setShowInquiryAnswers] = useState(false)

  // Elaboration
  const [elaborationText, setElaborationText] = useState('')
  const [elaborationChecks, setElaborationChecks] = useState<Record<number, boolean>>({})

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)

    Promise.all([
      api<TheoryResponse>(`/api/topics/${id}/theory`),
      api<TopicRelationship[]>(`/api/topics/${id}/relationships`),
    ])
      .then(([theoryData, relData]) => {
        setTheory(theoryData)
        setRelationships(relData)
        // Start at first incomplete stage
        const firstIncomplete = STAGES.findIndex(
          (s) => !isStageCompleted(theoryData.fire_progress, s)
        )
        if (firstIncomplete >= 0) {
          setCurrentStageIdx(firstIncomplete)
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  const currentStage = STAGES[currentStageIdx]

  const getStageContent = (stage: Stage): TheoryContentItem | null => {
    if (!theory) return null
    return theory.items.find((item) => item.content_type === stage) || null
  }

  const handleCompleteStage = async () => {
    if (!id || saving) return
    setSaving(true)

    try {
      const res = await api<FireProgressResponse>(`/api/topics/${id}/fire-progress`, {
        method: 'POST',
        body: JSON.stringify({ stage: currentStage }),
      })

      // Update local progress
      setTheory((prev) => {
        if (!prev) return prev
        const updated: FireProgress = {
          ...(prev.fire_progress || {
            fire_framework_completed: false,
            fire_inquiry_completed: false,
            fire_relationships_completed: false,
            fire_elaboration_completed: false,
            fire_completed_at: null,
          }),
          [`fire_${currentStage}_completed`]: true,
        }
        if (res.fire_completed_at) {
          updated.fire_completed_at = res.fire_completed_at
        }
        return { ...prev, fire_progress: updated }
      })

      if (res.all_stages_completed) {
        setXpEarned(res.xp_earned)
        setNewLevel(res.new_level_reached)
        setCompleted(true)
        if (res.xp_earned > 0) {
          useXpStore.getState().notifyXp(res.xp_earned)
          useAuthStore.getState().loadUser()
        }
        if (res.new_level_reached) {
          useXpStore.getState().showLevelUp(res.new_level_reached, getLevelName(res.new_level_reached))
        }
      } else {
        // Advance to next stage
        if (currentStageIdx < STAGES.length - 1) {
          setCurrentStageIdx(currentStageIdx + 1)
          // Reset stage-specific state
          setShowInquiryAnswers(false)
          setInquiryAnswers({})
          setElaborationText('')
          setElaborationChecks({})
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  const goToPrevStage = () => {
    if (currentStageIdx > 0) {
      setCurrentStageIdx(currentStageIdx - 1)
      setShowInquiryAnswers(false)
    }
  }

  // Parse inquiry questions from content (expects numbered list in markdown or JSON visual_assets)
  const parseInquiryQuestions = (content: TheoryContentItem): { question: string; answer: string }[] => {
    // Try visual_assets first (structured data)
    if (content.visual_assets && Array.isArray(content.visual_assets) && content.visual_assets.length > 0) {
      const questions = content.visual_assets as { question?: string; answer?: string }[]
      if (questions[0]?.question) {
        return questions.map((q) => ({
          question: q.question || '',
          answer: q.answer || '',
        }))
      }
    }
    // Fallback: parse markdown content for Q&A pairs
    return []
  }

  // Parse elaboration checklist from visual_assets or content
  const parseElaborationChecklist = (content: TheoryContentItem): string[] => {
    if (content.visual_assets && Array.isArray(content.visual_assets) && content.visual_assets.length > 0) {
      const items = content.visual_assets as (string | { item?: string; text?: string })[]
      if (typeof items[0] === 'string') return items as string[]
      if (typeof items[0] === 'object' && items[0] !== null) {
        return items.map((i) => {
          if (typeof i === 'string') return i
          return (i as { item?: string; text?: string }).item || (i as { item?: string; text?: string }).text || ''
        })
      }
    }
    return []
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-4 h-8 w-64 animate-pulse rounded bg-gray-200" />
        <div className="mb-6 flex gap-2">
          {STAGES.map((_, i) => (
            <div key={i} className="h-10 w-20 animate-pulse rounded-lg bg-gray-200" />
          ))}
        </div>
        <div className="h-64 animate-pulse rounded-xl border border-gray-200 bg-gray-50" />
      </div>
    )
  }

  if (error || !theory) {
    return (
      <div className="p-8">
        <Link to={`/topics/${id}`} className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline">
          &larr; Назад к теме
        </Link>
        <p className="mt-4 text-red-600">Ошибка загрузки: {error || 'Теория не найдена'}</p>
      </div>
    )
  }

  if (completed) {
    return (
      <div className="p-8">
        <div className="mx-auto max-w-lg text-center">
          <div className="mb-4 text-6xl">🔥</div>
          <h1 className="mb-2 text-2xl font-bold text-gray-900">Тема изучена!</h1>
          <p className="mb-2 text-gray-500">{theory.topic_title}</p>
          <p className="mb-6 text-sm text-gray-400">
            FIRe-flow пройден. SRS-карточки созданы для повторения.
          </p>

          {xpEarned > 0 && (
            <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-purple-100 px-4 py-2 text-lg font-bold text-purple-700">
              +{xpEarned} XP
            </div>
          )}
          {newLevel && (
            <p className="mb-6 text-sm font-medium text-green-600">
              Новый уровень: {newLevel}!
            </p>
          )}

          <div className="flex justify-center gap-3">
            <Link
              to={`/topics/${id}`}
              className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50"
            >
              К теме
            </Link>
            <Link
              to={`/topics/${id}/practice`}
              className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              Решать задания
            </Link>
            <button
              onClick={() => navigate('/dashboard')}
              className="rounded-lg bg-gray-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-gray-700"
            >
              На главную
            </button>
          </div>
        </div>
      </div>
    )
  }

  const stageContent = getStageContent(currentStage)
  const stageCompleted = isStageCompleted(theory.fire_progress, currentStage)

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <Link to={`/topics/${id}`} className="inline-flex items-center text-sm text-blue-600 hover:underline">
          &larr; Назад к теме
        </Link>
        <div className="text-sm text-gray-500">{theory.topic_title}</div>
      </div>

      {/* Stage progress bar */}
      <div className="mb-8">
        <div className="flex items-center gap-1">
          {STAGES.map((stage, idx) => {
            const done = isStageCompleted(theory.fire_progress, stage)
            const isCurrent = idx === currentStageIdx
            return (
              <div key={stage} className="flex flex-1 flex-col items-center">
                <button
                  onClick={() => setCurrentStageIdx(idx)}
                  className={`flex h-10 w-full items-center justify-center rounded-lg text-sm font-semibold transition-all ${
                    isCurrent
                      ? 'bg-orange-500 text-white shadow-md'
                      : done
                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                  }`}
                >
                  <span className="mr-1.5">{STAGE_SHORT[stage]}</span>
                  <span className="hidden sm:inline">{STAGE_LABELS[stage]}</span>
                  {done && !isCurrent && <span className="ml-1">&#10003;</span>}
                </button>
              </div>
            )
          })}
        </div>
        {/* Overall progress */}
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-gray-200">
          <div
            className="h-full rounded-full bg-orange-500 transition-all duration-300"
            style={{
              width: `${((currentStageIdx + (stageCompleted ? 1 : 0)) / STAGES.length) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Stage header */}
      <div className="mb-6">
        <h2 className="mb-1 text-xl font-bold text-gray-900">
          {STAGE_LABELS[currentStage]}
        </h2>
        <p className="text-sm text-gray-500">{STAGE_DESCRIPTIONS[currentStage]}</p>
      </div>

      {/* Stage content */}
      <div className="mb-8 rounded-xl border border-gray-200 bg-white p-6">
        {!stageContent ? (
          <p className="text-gray-400">
            Контент для этого этапа пока не добавлен. Вы можете отметить этап как пройденный и продолжить.
          </p>
        ) : currentStage === 'framework' ? (
          /* Framework: display theory with formulas */
          <div>
            <MathRenderer content={stageContent.content_markdown} />
          </div>
        ) : currentStage === 'inquiry' ? (
          /* Inquiry: questions + answer fields */
          <div>
            {stageContent.content_markdown && (
              <div className="mb-6">
                <MathRenderer content={stageContent.content_markdown} />
              </div>
            )}
            {(() => {
              const questions = parseInquiryQuestions(stageContent)
              if (questions.length === 0) return null
              return (
                <div className="space-y-6">
                  {questions.map((q, idx) => (
                    <div key={idx} className="rounded-lg border border-gray-100 bg-gray-50 p-4">
                      <p className="mb-3 font-medium text-gray-800">
                        {idx + 1}. {q.question}
                      </p>
                      <textarea
                        value={inquiryAnswers[idx] || ''}
                        onChange={(e) =>
                          setInquiryAnswers((prev) => ({ ...prev, [idx]: e.target.value }))
                        }
                        placeholder="Ваш ответ..."
                        rows={3}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-orange-400 focus:outline-none focus:ring-1 focus:ring-orange-400"
                      />
                      {showInquiryAnswers && q.answer && (
                        <div className="mt-3 rounded-lg border border-green-200 bg-green-50 p-3">
                          <p className="mb-1 text-xs font-semibold text-green-700">Эталонный ответ:</p>
                          <div className="text-sm text-green-800">
                            <MathRenderer content={q.answer} />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  {!showInquiryAnswers && (
                    <button
                      onClick={() => setShowInquiryAnswers(true)}
                      className="rounded-lg border border-orange-300 px-4 py-2 text-sm font-medium text-orange-600 transition-colors hover:bg-orange-50"
                    >
                      Показать эталонные ответы
                    </button>
                  )}
                </div>
              )
            })()}
          </div>
        ) : currentStage === 'relationships' ? (
          /* Relationships: related topics list + notes */
          <div>
            {stageContent.content_markdown && (
              <div className="mb-6">
                <MathRenderer content={stageContent.content_markdown} />
              </div>
            )}
            {relationships.length > 0 && (
              <div>
                <h3 className="mb-3 text-sm font-semibold text-gray-700">Связанные темы:</h3>
                <div className="space-y-2">
                  {relationships.map((rel) =>
                    rel.related_topic ? (
                      <div
                        key={rel.id}
                        className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
                      >
                        <div>
                          <span className="mr-2 font-semibold text-blue-600">
                            #{rel.related_topic.task_number}
                          </span>
                          <span className="text-gray-700">{rel.related_topic.title}</span>
                          {rel.relationship_type && (
                            <span className="ml-2 text-xs text-gray-400">
                              ({rel.relationship_type === 'prerequisite' ? 'пререквизит' : rel.relationship_type})
                            </span>
                          )}
                        </div>
                        <Link
                          to={`/topics/${rel.related_topic.id}`}
                          className="text-sm text-blue-500 hover:underline"
                        >
                          Открыть
                        </Link>
                      </div>
                    ) : null
                  )}
                </div>
              </div>
            )}
          </div>
        ) : currentStage === 'elaboration' ? (
          /* Elaboration: explain in your own words + checklist */
          <div>
            {stageContent.content_markdown && (
              <div className="mb-6">
                <MathRenderer content={stageContent.content_markdown} />
              </div>
            )}
            <div className="mb-6">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Объясните тему простым языком:
              </label>
              <textarea
                value={elaborationText}
                onChange={(e) => setElaborationText(e.target.value)}
                placeholder="Представьте, что объясняете другу, который не знает математику..."
                rows={5}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-orange-400 focus:outline-none focus:ring-1 focus:ring-orange-400"
              />
            </div>
            {(() => {
              const checklist = parseElaborationChecklist(stageContent)
              if (checklist.length === 0) return null
              return (
                <div>
                  <h3 className="mb-3 text-sm font-semibold text-gray-700">
                    Чек-лист ключевых пунктов:
                  </h3>
                  <div className="space-y-2">
                    {checklist.map((item, idx) => (
                      <label
                        key={idx}
                        className="flex cursor-pointer items-start gap-3 rounded-lg border border-gray-100 bg-gray-50 p-3 transition-colors hover:bg-gray-100"
                      >
                        <input
                          type="checkbox"
                          checked={elaborationChecks[idx] || false}
                          onChange={(e) =>
                            setElaborationChecks((prev) => ({
                              ...prev,
                              [idx]: e.target.checked,
                            }))
                          }
                          className="mt-0.5 h-4 w-4 rounded border-gray-300 text-orange-500 focus:ring-orange-400"
                        />
                        <span className="text-sm text-gray-700">{item}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )
            })()}
          </div>
        ) : null}
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center justify-between">
        <button
          onClick={goToPrevStage}
          disabled={currentStageIdx === 0}
          className={`rounded-lg border px-5 py-2.5 text-sm font-semibold transition-colors ${
            currentStageIdx === 0
              ? 'cursor-not-allowed border-gray-200 text-gray-300'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
        >
          &larr; Назад
        </button>

        <button
          onClick={handleCompleteStage}
          disabled={saving}
          className="rounded-lg bg-orange-500 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-orange-600 disabled:opacity-50"
        >
          {saving
            ? 'Сохранение...'
            : currentStageIdx === STAGES.length - 1
              ? 'Завершить FIRe-flow'
              : stageCompleted
                ? 'Далее →'
                : 'Завершить этап и далее →'}
        </button>
      </div>

      {/* Stage completed indicator */}
      {stageCompleted && (
        <p className="mt-4 text-center text-sm text-green-600">
          &#10003; Этот этап уже пройден
        </p>
      )}
    </div>
  )
}
