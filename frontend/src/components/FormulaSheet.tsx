import { useEffect, useRef, useState, useCallback } from 'react'
import { useFormulaStore } from '../stores/formulaStore'
import allFormulas from '../data/formulas'
import MathRenderer from './MathRenderer'

const MIN_WIDTH = 360
const DEFAULT_WIDTH_RATIO = 0.42

export default function FormulaSheet() {
  const { isOpen, activeTaskNumber, close, toggle } = useFormulaStore()
  const panelRef = useRef<HTMLDivElement>(null)
  const [selectedTask, setSelectedTask] = useState<number | null>(null)
  const [panelWidth, setPanelWidth] = useState(() =>
    Math.max(MIN_WIDTH, Math.round(window.innerWidth * DEFAULT_WIDTH_RATIO)),
  )
  const isResizing = useRef(false)

  // Sync selectedTask with activeTaskNumber when modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedTask(activeTaskNumber)
    }
  }, [isOpen, activeTaskNumber])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) close()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isOpen, close])

  // Resize handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isResizing.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return
      const newWidth = window.innerWidth - e.clientX
      setPanelWidth(Math.max(MIN_WIDTH, Math.min(newWidth, window.innerWidth * 0.85)))
    }

    const handleMouseUp = () => {
      isResizing.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
  }, [])

  const formulasToShow = selectedTask
    ? allFormulas.filter((f) => f.taskNumber === selectedTask)
    : allFormulas

  return (
    <>
      {/* Floating button */}
      <button
        onClick={toggle}
        className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg transition-all hover:scale-110 hover:shadow-xl active:scale-95"
        title="Формулы"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
          <path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4z" />
          <path d="M17 14v6M14 17h6" />
        </svg>
      </button>

      {/* Side panel */}
      {isOpen && (
        <>
          {/* Panel — no backdrop, main content stays interactive */}
          <div
            ref={panelRef}
            className="fixed inset-y-0 right-0 z-50 flex flex-col border-l border-gray-200 bg-white shadow-2xl dark:border-gray-700 dark:bg-gray-800"
            style={{ width: panelWidth }}
          >
            {/* Resize handle */}
            <div
              onMouseDown={handleMouseDown}
              className="absolute inset-y-0 left-0 z-10 w-1.5 cursor-col-resize bg-transparent transition-colors hover:bg-indigo-400/50"
            />

            {/* Header */}
            <div className="flex items-center justify-between bg-gradient-to-r from-indigo-500 to-purple-600 px-5 py-3">
              <h2 className="truncate text-base font-bold text-white">
                {selectedTask
                  ? `Задание ${selectedTask} — ${allFormulas.find((f) => f.taskNumber === selectedTask)?.title || ''}`
                  : 'Все формулы ЕГЭ'}
              </h2>
              <button
                onClick={close}
                className="ml-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white/80 transition-colors hover:bg-white/20 hover:text-white"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Task tabs */}
            <div className="flex flex-wrap gap-1.5 border-b border-gray-200 bg-gray-50 px-4 py-2.5 dark:border-gray-700 dark:bg-gray-900/50">
              <button
                onClick={() => setSelectedTask(null)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                  selectedTask === null
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-gray-600 hover:bg-gray-200 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                Все
              </button>
              {allFormulas.map((f) => (
                <button
                  key={f.taskNumber}
                  onClick={() => setSelectedTask(f.taskNumber)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                    selectedTask === f.taskNumber
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-gray-600 hover:bg-gray-200 dark:text-gray-400 dark:hover:bg-gray-700'
                  }`}
                >
                  {f.taskNumber}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-5 py-5">
              <div className="space-y-8">
                {formulasToShow.map((task) => (
                  <div key={task.taskNumber}>
                    {/* Task title - only show when viewing all */}
                    {!selectedTask && (
                      <div className="mb-4 flex items-center gap-3">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
                          {task.taskNumber}
                        </span>
                        <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">
                          {task.title}
                        </h3>
                      </div>
                    )}

                    <div className="space-y-4">
                      {task.sections.map((section, si) => (
                        <div
                          key={si}
                          className="rounded-xl border border-gray-200 bg-gray-50/50 p-4 dark:border-gray-700 dark:bg-gray-900/30"
                        >
                          <h4 className="mb-3 text-sm font-semibold text-indigo-700 dark:text-indigo-400">
                            {section.title}
                          </h4>
                          <div className="space-y-2">
                            {section.formulas.map((formula, fi) => (
                              <div
                                key={fi}
                                className="text-sm text-gray-800 dark:text-gray-200"
                              >
                                <MathRenderer content={formula} />
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Divider between tasks when viewing all */}
                    {!selectedTask && (
                      <div className="mt-6 border-b border-gray-200 dark:border-gray-700" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}
