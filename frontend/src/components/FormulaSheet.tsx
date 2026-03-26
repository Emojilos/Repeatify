import { useEffect, useRef, useState } from 'react'
import { useFormulaStore } from '../stores/formulaStore'
import allFormulas from '../data/formulas'
import MathRenderer from './MathRenderer'

export default function FormulaSheet() {
  const { isOpen, activeTaskNumber, close, toggle } = useFormulaStore()
  const modalRef = useRef<HTMLDivElement>(null)
  const [selectedTask, setSelectedTask] = useState<number | null>(null)

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

      {/* Modal overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={close}
          />

          {/* Modal */}
          <div
            ref={modalRef}
            className="relative flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-gray-800"
            style={{ animation: 'formula-in 0.25s ease-out' }}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-gray-200 bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-bold text-white">
                  {selectedTask
                    ? `Задание ${selectedTask} — ${allFormulas.find((f) => f.taskNumber === selectedTask)?.title || ''}`
                    : 'Все формулы ЕГЭ'}
                </h2>
              </div>
              <button
                onClick={close}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-white/80 transition-colors hover:bg-white/20 hover:text-white"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Task tabs */}
            <div className="flex gap-1.5 overflow-x-auto border-b border-gray-200 bg-gray-50 px-4 py-2.5 dark:border-gray-700 dark:bg-gray-900/50">
              <button
                onClick={() => setSelectedTask(null)}
                className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
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
                  className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
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
            <div className="flex-1 overflow-y-auto px-6 py-5">
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
        </div>
      )}
    </>
  )
}
