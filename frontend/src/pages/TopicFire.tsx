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

interface Prototype {
  id: string
  task_number: number
  prototype_code: string
  title: string
  description: string | null
  difficulty_within_task: string
  estimated_study_minutes: number | null
  theory_markdown: string | null
  key_formulas: { name?: string; formula?: string; description?: string }[] | null
  solution_algorithm: { step?: number; title?: string; description?: string }[] | null
  common_mistakes: { mistake?: string; correct?: string; explanation?: string }[] | null
  related_prototypes: { prototype_code?: string; title?: string; relationship?: string }[] | null
  order_index: number | null
}

interface PrototypeListItem {
  id: string
  task_number: number
  prototype_code: string
  title: string
  description: string | null
  difficulty_within_task: string
  estimated_study_minutes: number | null
  order_index: number | null
}

interface PrototypeListResponse {
  items: PrototypeListItem[]
  total: number
}

interface TopicInfo {
  id: string
  task_number: number
  title: string
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
  framework: 'Изучите теорию и ключевые формулы прототипа',
  inquiry: 'Разберите алгоритм решения и ключевые формулы',
  relationships: 'Изучите связи с другими прототипами и темами',
  elaboration: 'Проверьте понимание — разберите типичные ошибки',
}

function isStageCompleted(progress: FireProgress | null, stage: Stage): boolean {
  if (!progress) return false
  const key = `fire_${stage}_completed` as keyof FireProgress
  return progress[key] === true
}

function difficultyBadge(level: string) {
  const styles: Record<string, string> = {
    easy: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
    hard: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  }
  const labels: Record<string, string> = { easy: 'Легко', medium: 'Средне', hard: 'Сложно' }
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${styles[level] || styles.medium}`}>
      {labels[level] || level}
    </span>
  )
}

export default function TopicFire() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  // Topic-level data (theory_content based — fallback)
  const [theory, setTheory] = useState<TheoryResponse | null>(null)
  const [relationships, setRelationships] = useState<TopicRelationship[]>([])

  // Prototype-based flow
  const [prototypes, setPrototypes] = useState<PrototypeListItem[]>([])
  const [selectedPrototype, setSelectedPrototype] = useState<Prototype | null>(null)
  const [usePrototypeFlow, setUsePrototypeFlow] = useState(false)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentStageIdx, setCurrentStageIdx] = useState(0)
  const [saving, setSaving] = useState(false)
  const [completed, setCompleted] = useState(false)
  const [xpEarned, setXpEarned] = useState(0)
  const [newLevel, setNewLevel] = useState<number | null>(null)

  // Inquiry stage state
  const [inquiryAnswers, setInquiryAnswers] = useState<Record<number, string>>({})
  const [showInquiryAnswers, setShowInquiryAnswers] = useState(false)
  // Elaboration stage state
  const [elaborationText, setElaborationText] = useState('')
  const [elaborationChecks, setElaborationChecks] = useState<Record<number, boolean>>({})

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)

    // Load topic theory + relationships + topic info in parallel
    Promise.all([
      api<TheoryResponse>(`/api/topics/${id}/theory`),
      api<TopicRelationship[]>(`/api/topics/${id}/relationships`),
    ])
      .then(async ([theoryData, relData]) => {
        setTheory(theoryData)
        setRelationships(relData)

        // Get task_number from topic to fetch prototypes
        const topicRes = await api<TopicInfo>(`/api/topics/${id}`)
        const protoRes = await api<PrototypeListResponse>(
          `/api/prototypes?task_number=${topicRes.task_number}`
        )
        setPrototypes(protoRes.items)

        // Use prototype flow if prototypes exist
        if (protoRes.items.length > 0) {
          setUsePrototypeFlow(true)
        } else {
          // Fallback: use legacy theory_content flow
          const firstIncomplete = STAGES.findIndex(
            (s) => !isStageCompleted(theoryData.fire_progress, s)
          )
          if (firstIncomplete >= 0) {
            setCurrentStageIdx(firstIncomplete)
          }
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  const currentStage = STAGES[currentStageIdx]

  const selectPrototype = async (protoId: string) => {
    try {
      setLoading(true)
      const detail = await api<Prototype>(`/api/prototypes/${protoId}`)
      setSelectedPrototype(detail)
      setCurrentStageIdx(0)
      resetStageState()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки прототипа')
    } finally {
      setLoading(false)
    }
  }

  const backToPrototypeList = () => {
    setSelectedPrototype(null)
    setCurrentStageIdx(0)
    setCompleted(false)
    resetStageState()
  }

  const resetStageState = () => {
    setShowInquiryAnswers(false)
    setInquiryAnswers({})
    setElaborationText('')
    setElaborationChecks({})
  }

  // --- Legacy theory_content helpers ---
  const getStageContent = (stage: Stage): TheoryContentItem | null => {
    if (!theory) return null
    return theory.items.find((item) => item.content_type === stage) || null
  }

  const parseInquiryQuestions = (content: TheoryContentItem): { question: string; answer: string }[] => {
    if (content.visual_assets && Array.isArray(content.visual_assets) && content.visual_assets.length > 0) {
      const questions = content.visual_assets as { question?: string; answer?: string }[]
      if (questions[0]?.question) {
        return questions.map((q) => ({
          question: q.question || '',
          answer: q.answer || '',
        }))
      }
    }
    return []
  }

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

  // --- Stage completion handler ---
  const handleCompleteStage = async () => {
    if (!id || saving) return
    setSaving(true)

    try {
      const res = await api<FireProgressResponse>(`/api/topics/${id}/fire-progress`, {
        method: 'POST',
        body: JSON.stringify({ stage: currentStage }),
      })

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
        if (currentStageIdx < STAGES.length - 1) {
          setCurrentStageIdx(currentStageIdx + 1)
          resetStageState()
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

  // --- Loading ---
  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-4 h-8 w-64 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="mb-6 flex gap-2">
          {STAGES.map((_, i) => (
            <div key={i} className="h-10 w-20 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700" />
          ))}
        </div>
        <div className="h-64 animate-pulse rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
      </div>
    )
  }

  // --- Error ---
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

  // --- Completion screen ---
  if (completed) {
    const completedTitle = selectedPrototype
      ? `${selectedPrototype.prototype_code} — ${selectedPrototype.title}`
      : theory.topic_title

    return (
      <div className="p-8">
        <div className="mx-auto max-w-lg text-center">
          <div className="mb-4 text-6xl">🔥</div>
          <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-gray-100">
            {selectedPrototype ? 'Прототип изучен!' : 'Тема изучена!'}
          </h1>
          <p className="mb-2 text-gray-500 dark:text-gray-400">{completedTitle}</p>
          <p className="mb-6 text-sm text-gray-400 dark:text-gray-500">
            FIRe-flow пройден. FSRS-карточки созданы для повторения.
          </p>

          {xpEarned > 0 && (
            <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-purple-100 px-4 py-2 text-lg font-bold text-purple-700 dark:bg-purple-900/40 dark:text-purple-300">
              +{xpEarned} XP
            </div>
          )}
          {newLevel && (
            <p className="mb-6 text-sm font-medium text-green-600">
              Новый уровень: {newLevel}!
            </p>
          )}

          <div className="flex flex-wrap justify-center gap-3">
            {selectedPrototype && prototypes.length > 1 && (
              <button
                onClick={backToPrototypeList}
                className="rounded-lg border border-orange-300 px-5 py-2.5 text-sm font-semibold text-orange-600 transition-colors hover:bg-orange-50 dark:border-orange-700 dark:text-orange-400 dark:hover:bg-orange-900/30"
              >
                Другие прототипы
              </button>
            )}
            <Link
              to={`/topics/${id}`}
              className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              К теме
            </Link>
            {selectedPrototype && (
              <Link
                to={`/prototypes/${selectedPrototype.id}`}
                className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
              >
                Практика
              </Link>
            )}
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

  // --- Prototype selection screen ---
  if (usePrototypeFlow && !selectedPrototype) {
    return (
      <div className="p-8">
        <div className="mb-6 flex items-center justify-between">
          <Link to={`/topics/${id}`} className="inline-flex items-center text-sm text-blue-600 hover:underline">
            &larr; Назад к теме
          </Link>
          <div className="text-sm text-gray-500 dark:text-gray-400">{theory.topic_title}</div>
        </div>

        <h1 className="mb-2 text-xl font-bold text-gray-900 dark:text-gray-100">
          Выберите прототип для изучения
        </h1>
        <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
          Каждый прототип — отдельный тип задачи. Пройдите FIRe-flow для глубокого понимания.
        </p>

        <div className="grid gap-4 sm:grid-cols-2">
          {prototypes.map((proto) => (
            <button
              key={proto.id}
              onClick={() => selectPrototype(proto.id)}
              className="rounded-xl border border-gray-200 bg-white p-5 text-left transition-all hover:border-orange-300 hover:shadow-md dark:border-gray-700 dark:bg-gray-800 dark:hover:border-orange-600"
            >
              <div className="mb-2 flex items-center gap-2">
                <span className="text-lg font-bold text-orange-500">{proto.prototype_code}</span>
                {difficultyBadge(proto.difficulty_within_task)}
              </div>
              <h3 className="mb-1 font-semibold text-gray-900 dark:text-gray-100">{proto.title}</h3>
              {proto.description && (
                <p className="mb-2 text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{proto.description}</p>
              )}
              {proto.estimated_study_minutes && (
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  ~{proto.estimated_study_minutes} мин
                </p>
              )}
            </button>
          ))}
        </div>
      </div>
    )
  }

  // --- FIRe wizard ---
  const stageCompleted = isStageCompleted(theory.fire_progress, currentStage)
  const topicTitle = selectedPrototype
    ? `${selectedPrototype.prototype_code} — ${selectedPrototype.title}`
    : theory.topic_title

  // Render stage content based on whether we're in prototype flow or legacy flow
  const renderStageContent = () => {
    if (selectedPrototype) {
      return renderPrototypeStageContent()
    }
    return renderLegacyStageContent()
  }

  const renderPrototypeStageContent = () => {
    if (!selectedPrototype) return null

    switch (currentStage) {
      case 'framework':
        return (
          <div>
            {selectedPrototype.theory_markdown ? (
              <MathRenderer content={selectedPrototype.theory_markdown} />
            ) : (
              <p className="text-gray-400 dark:text-gray-500">
                Теория для этого прототипа пока не добавлена.
              </p>
            )}
          </div>
        )

      case 'inquiry':
        return (
          <div>
            {/* Key formulas */}
            {selectedPrototype.key_formulas && selectedPrototype.key_formulas.length > 0 && (
              <div className="mb-6">
                <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Ключевые формулы:
                </h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  {selectedPrototype.key_formulas.map((f, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-blue-100 bg-blue-50 p-3 dark:border-blue-900 dark:bg-blue-900/20"
                    >
                      {f.name && (
                        <p className="mb-1 text-xs font-semibold text-blue-700 dark:text-blue-300">{f.name}</p>
                      )}
                      {f.formula && (
                        <div className="text-sm">
                          <MathRenderer content={f.formula} />
                        </div>
                      )}
                      {f.description && (
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{f.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Solution algorithm */}
            {selectedPrototype.solution_algorithm && selectedPrototype.solution_algorithm.length > 0 && (
              <div>
                <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Алгоритм решения:
                </h3>
                <div className="space-y-3">
                  {selectedPrototype.solution_algorithm.map((step, idx) => (
                    <div key={idx} className="flex gap-3">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-orange-100 text-sm font-bold text-orange-600 dark:bg-orange-900/40 dark:text-orange-300">
                        {step.step || idx + 1}
                      </div>
                      <div>
                        {step.title && (
                          <p className="font-medium text-gray-800 dark:text-gray-200">{step.title}</p>
                        )}
                        {step.description && (
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            <MathRenderer content={step.description} />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!selectedPrototype.key_formulas?.length && !selectedPrototype.solution_algorithm?.length && (
              <p className="text-gray-400 dark:text-gray-500">
                Контент для этого этапа пока не добавлен.
              </p>
            )}
          </div>
        )

      case 'relationships':
        return (
          <div>
            {/* Related prototypes from prototype data */}
            {selectedPrototype.related_prototypes && selectedPrototype.related_prototypes.length > 0 && (
              <div className="mb-6">
                <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Связанные прототипы:
                </h3>
                <div className="space-y-2">
                  {selectedPrototype.related_prototypes.map((rp, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-900"
                    >
                      <div>
                        <span className="mr-2 font-semibold text-orange-500">{rp.prototype_code}</span>
                        <span className="text-gray-700 dark:text-gray-300">{rp.title}</span>
                        {rp.relationship && (
                          <span className="ml-2 text-xs text-gray-400 dark:text-gray-500">
                            ({rp.relationship})
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Also show topic-level relationships */}
            {relationships.length > 0 && (
              <div>
                <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">Связанные темы:</h3>
                <div className="space-y-2">
                  {relationships.map((rel) =>
                    rel.related_topic ? (
                      <div
                        key={rel.id}
                        className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-900"
                      >
                        <div>
                          <span className="mr-2 font-semibold text-blue-600">
                            #{rel.related_topic.task_number}
                          </span>
                          <span className="text-gray-700 dark:text-gray-300">{rel.related_topic.title}</span>
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

            {!selectedPrototype.related_prototypes?.length && relationships.length === 0 && (
              <p className="text-gray-400 dark:text-gray-500">Связи пока не добавлены.</p>
            )}
          </div>
        )

      case 'elaboration':
        return (
          <div>
            {/* Common mistakes */}
            {selectedPrototype.common_mistakes && selectedPrototype.common_mistakes.length > 0 && (
              <div className="mb-6">
                <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Типичные ошибки — проверьте, что вы их не допускаете:
                </h3>
                <div className="space-y-3">
                  {selectedPrototype.common_mistakes.map((cm, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-red-100 bg-red-50 p-4 dark:border-red-900 dark:bg-red-900/20"
                    >
                      {cm.mistake && (
                        <div className="mb-2">
                          <span className="text-xs font-semibold text-red-600 dark:text-red-400">Ошибка: </span>
                          <span className="text-sm text-red-700 dark:text-red-300">{cm.mistake}</span>
                        </div>
                      )}
                      {cm.correct && (
                        <div className="mb-1">
                          <span className="text-xs font-semibold text-green-600 dark:text-green-400">Правильно: </span>
                          <span className="text-sm text-green-700 dark:text-green-300">{cm.correct}</span>
                        </div>
                      )}
                      {cm.explanation && (
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{cm.explanation}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Self-explanation */}
            <div className="mb-6">
              <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Объясните этот прототип своими словами:
              </label>
              <textarea
                value={elaborationText}
                onChange={(e) => setElaborationText(e.target.value)}
                placeholder="Опишите алгоритм решения задач этого типа..."
                rows={5}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-orange-400 focus:outline-none focus:ring-1 focus:ring-orange-400 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
              />
            </div>

            {/* Checklist from key formulas as comprehension check */}
            {selectedPrototype.key_formulas && selectedPrototype.key_formulas.length > 0 && (
              <div>
                <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Чек-лист понимания:
                </h3>
                <div className="space-y-2">
                  {selectedPrototype.key_formulas.map((f, idx) => (
                    <label
                      key={idx}
                      className="flex cursor-pointer items-start gap-3 rounded-lg border border-gray-100 bg-gray-50 p-3 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800"
                    >
                      <input
                        type="checkbox"
                        checked={elaborationChecks[idx] || false}
                        onChange={(e) =>
                          setElaborationChecks((prev) => ({ ...prev, [idx]: e.target.checked }))
                        }
                        className="mt-0.5 h-4 w-4 rounded border-gray-300 text-orange-500 focus:ring-orange-400"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        Могу объяснить: {f.name || f.formula || `Формула ${idx + 1}`}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        )

      default:
        return null
    }
  }

  const renderLegacyStageContent = () => {
    const stageContent = getStageContent(currentStage)

    if (!stageContent) {
      return (
        <p className="text-gray-400 dark:text-gray-500">
          Контент для этого этапа пока не добавлен. Вы можете отметить этап как пройденный и продолжить.
        </p>
      )
    }

    switch (currentStage) {
      case 'framework':
        return <MathRenderer content={stageContent.content_markdown} />

      case 'inquiry':
        return (
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
                    <div key={idx} className="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900">
                      <p className="mb-3 font-medium text-gray-800 dark:text-gray-200">
                        {idx + 1}. {q.question}
                      </p>
                      <textarea
                        value={inquiryAnswers[idx] || ''}
                        onChange={(e) =>
                          setInquiryAnswers((prev) => ({ ...prev, [idx]: e.target.value }))
                        }
                        placeholder="Ваш ответ..."
                        rows={3}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-orange-400 focus:outline-none focus:ring-1 focus:ring-orange-400 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                      />
                      {showInquiryAnswers && q.answer && (
                        <div className="mt-3 rounded-lg border border-green-200 bg-green-50 p-3 dark:border-green-800 dark:bg-green-900/30">
                          <p className="mb-1 text-xs font-semibold text-green-700 dark:text-green-300">Эталонный ответ:</p>
                          <div className="text-sm text-green-800 dark:text-green-200">
                            <MathRenderer content={q.answer} />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  {!showInquiryAnswers && (
                    <button
                      onClick={() => setShowInquiryAnswers(true)}
                      className="rounded-lg border border-orange-300 px-4 py-2 text-sm font-medium text-orange-600 transition-colors hover:bg-orange-50 dark:border-orange-700 dark:text-orange-400 dark:hover:bg-orange-900/30"
                    >
                      Показать эталонные ответы
                    </button>
                  )}
                </div>
              )
            })()}
          </div>
        )

      case 'relationships':
        return (
          <div>
            {stageContent.content_markdown && (
              <div className="mb-6">
                <MathRenderer content={stageContent.content_markdown} />
              </div>
            )}
            {relationships.length > 0 && (
              <div>
                <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">Связанные темы:</h3>
                <div className="space-y-2">
                  {relationships.map((rel) =>
                    rel.related_topic ? (
                      <div
                        key={rel.id}
                        className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-900"
                      >
                        <div>
                          <span className="mr-2 font-semibold text-blue-600">
                            #{rel.related_topic.task_number}
                          </span>
                          <span className="text-gray-700 dark:text-gray-300">{rel.related_topic.title}</span>
                          {rel.relationship_type && (
                            <span className="ml-2 text-xs text-gray-400 dark:text-gray-500">
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
        )

      case 'elaboration':
        return (
          <div>
            {stageContent.content_markdown && (
              <div className="mb-6">
                <MathRenderer content={stageContent.content_markdown} />
              </div>
            )}
            <div className="mb-6">
              <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Объясните тему простым языком:
              </label>
              <textarea
                value={elaborationText}
                onChange={(e) => setElaborationText(e.target.value)}
                placeholder="Представьте, что объясняете другу, который не знает математику..."
                rows={5}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-orange-400 focus:outline-none focus:ring-1 focus:ring-orange-400 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
              />
            </div>
            {(() => {
              const checklist = parseElaborationChecklist(stageContent)
              if (checklist.length === 0) return null
              return (
                <div>
                  <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Чек-лист ключевых пунктов:
                  </h3>
                  <div className="space-y-2">
                    {checklist.map((item, idx) => (
                      <label
                        key={idx}
                        className="flex cursor-pointer items-start gap-3 rounded-lg border border-gray-100 bg-gray-50 p-3 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800"
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
                        <span className="text-sm text-gray-700 dark:text-gray-300">{item}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )
            })()}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        {selectedPrototype ? (
          <button
            onClick={backToPrototypeList}
            className="inline-flex items-center text-sm text-blue-600 hover:underline"
          >
            &larr; К списку прототипов
          </button>
        ) : (
          <Link to={`/topics/${id}`} className="inline-flex items-center text-sm text-blue-600 hover:underline">
            &larr; Назад к теме
          </Link>
        )}
        <div className="text-sm text-gray-500 dark:text-gray-400">{topicTitle}</div>
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
                        ? 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/40 dark:text-green-300 dark:hover:bg-green-900/60'
                        : 'bg-gray-100 text-gray-400 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-500 dark:hover:bg-gray-700'
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
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
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
        <h2 className="mb-1 text-xl font-bold text-gray-900 dark:text-gray-100">
          {STAGE_LABELS[currentStage]}
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">{STAGE_DESCRIPTIONS[currentStage]}</p>
      </div>

      {/* Stage content */}
      <div className="mb-8 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        {renderStageContent()}
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center justify-between">
        <button
          onClick={goToPrevStage}
          disabled={currentStageIdx === 0}
          className={`rounded-lg border px-5 py-2.5 text-sm font-semibold transition-colors ${
            currentStageIdx === 0
              ? 'cursor-not-allowed border-gray-200 text-gray-300 dark:border-gray-700 dark:text-gray-600'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
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
                ? 'Далее \u2192'
                : 'Завершить этап и далее \u2192'}
        </button>
      </div>

      {stageCompleted && (
        <p className="mt-4 text-center text-sm text-green-600">
          &#10003; Этот этап уже пройден
        </p>
      )}
    </div>
  )
}
