import { useState } from 'react'
import LatexRenderer from '../../../components/math/LatexRenderer.jsx'

export default function StepByStepReveal({ steps = [], onHintsUsedChange }) {
  const [revealedCount, setRevealedCount] = useState(0)

  const revealNext = () => {
    const next = revealedCount + 1
    setRevealedCount(next)
    onHintsUsedChange?.(next)
  }

  const allRevealed = revealedCount >= steps.length

  return (
    <div className="w-full max-w-2xl mx-auto mt-4 space-y-3">
      {steps.slice(0, revealedCount).map((step, i) => (
        <div
          key={step.step_number ?? i}
          className="rounded-lg border border-gray-200 bg-gray-50 p-4 animate-reveal"
        >
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-xs font-semibold text-gray-400">
              {step.step_number ?? i + 1}
            </span>
            <h4 className="font-semibold text-gray-800 text-sm">
              {step.title}
            </h4>
          </div>

          {step.text && (
            <div className="text-[16px] leading-relaxed text-gray-700 mt-1">
              <LatexRenderer text={step.text} />
            </div>
          )}

          {step.latex && (
            <div className="mt-2 overflow-x-auto text-center">
              <LatexRenderer text={`$$${step.latex}$$`} />
            </div>
          )}

          {step.hint && (
            <p className="mt-2 text-xs text-gray-400 italic">
              {step.hint}
            </p>
          )}
        </div>
      ))}

      {!allRevealed && (
        <button
          onClick={revealNext}
          className="w-full py-3 rounded-lg border-2 border-dashed border-gray-300
                     text-gray-500 font-medium text-sm
                     hover:border-gray-400 hover:text-gray-700
                     transition-colors duration-150 cursor-pointer"
        >
          Показать шаг {revealedCount + 1} из {steps.length}
        </button>
      )}
    </div>
  )
}
