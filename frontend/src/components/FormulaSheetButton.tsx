import { useFormulaStore } from '../stores/formulaStore'

export default function FormulaSheetButton() {
  const toggle = useFormulaStore((s) => s.toggle)

  return (
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
  )
}
