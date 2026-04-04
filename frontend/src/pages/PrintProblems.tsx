import { useEffect, useState, useRef } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { api } from '../lib/api'
import ProblemContent from '../components/ProblemContent'

interface Problem {
  id: string
  topic_id: string
  task_number: number
  difficulty: string
  problem_text: string
  problem_images?: string[] | null
  source: string | null
  max_points: number | null
}

interface ProblemListResponse {
  items: Problem[]
  total: number
  page: number
  page_size: number
}

export default function PrintProblems() {
  const [searchParams, setSearchParams] = useSearchParams()
  const taskNumber = parseInt(searchParams.get('task') || '1', 10)
  const count = parseInt(searchParams.get('count') || '10', 10)

  const [problems, setProblems] = useState<Problem[]>([])
  const [totalAvailable, setTotalAvailable] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fetched, setFetched] = useState(false)

  // Form state (before fetching)
  const [formTask, setFormTask] = useState(taskNumber)
  const [formCount, setFormCount] = useState(count)

  const printRef = useRef<HTMLDivElement>(null)

  function handleGenerate() {
    setSearchParams({ task: String(formTask), count: String(formCount) })
  }

  useEffect(() => {
    const task = parseInt(searchParams.get('task') || '0', 10)
    const cnt = parseInt(searchParams.get('count') || '0', 10)
    if (!task || !cnt) return

    setFormTask(task)
    setFormCount(cnt)
    setLoading(true)
    setError(null)

    api<ProblemListResponse>(`/api/problems?task_number=${task}&page_size=${cnt}`)
      .then((data) => {
        setProblems(data.items)
        setTotalAvailable(data.total)
        setFetched(true)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [searchParams])

  function handlePrint() {
    window.print()
  }

  return (
    <div>
      {/* Controls — hidden when printing */}
      <div className="print:hidden p-8">
        <Link to="/topics" className="mb-4 inline-flex items-center text-sm text-blue-600 hover:underline dark:text-blue-400">
          &larr; Все темы
        </Link>

        <h1 className="mb-6 text-2xl font-bold text-gray-900 dark:text-gray-100">Печать заданий</h1>

        <div className="mb-6 flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Номер задания
            </label>
            <select
              value={formTask}
              onChange={(e) => setFormTask(Number(e.target.value))}
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            >
              {Array.from({ length: 19 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>Задание {n}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Количество
            </label>
            <input
              type="number"
              min={1}
              max={100}
              value={formCount}
              onChange={(e) => setFormCount(Math.max(1, Math.min(100, Number(e.target.value))))}
              className="w-24 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>

          <button
            onClick={handleGenerate}
            className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Сгенерировать
          </button>

          {fetched && problems.length > 0 && (
            <button
              onClick={handlePrint}
              className="rounded-lg border border-gray-300 bg-white px-5 py-2 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
            >
              Распечатать
            </button>
          )}
        </div>

        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800" />
            ))}
          </div>
        )}

        {error && <p className="text-red-600">{error}</p>}

        {fetched && !loading && (
          <p className="mb-4 text-sm text-gray-500 dark:text-gray-400">
            Показано {problems.length} из {totalAvailable} доступных заданий
          </p>
        )}
      </div>

      {/* Printable area */}
      {fetched && problems.length > 0 && (
        <div ref={printRef} className="print:p-0 px-8 pb-8">
          {/* Print header — visible only when printing */}
          <div className="hidden print:block mb-6">
            <h1 className="text-xl font-bold">Задание {formTask} — Вариант ({problems.length} задач)</h1>
            <div className="mt-1 text-sm text-gray-500">Repeatify</div>
          </div>

          <div className="space-y-6 print:space-y-4">
            {problems.map((problem, idx) => (
              <div
                key={problem.id}
                className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800 print:rounded-none print:border-0 print:border-b print:border-gray-300 print:p-4 print:bg-white"
                style={{ pageBreakInside: 'avoid' }}
              >
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-sm font-bold text-gray-900 dark:text-gray-100 print:text-black">
                    {idx + 1}.
                  </span>
                </div>
                <div className="text-sm text-gray-800 dark:text-gray-200 print:text-black">
                  <ProblemContent
                    text={problem.problem_text}
                    images={problem.problem_images}
                    imageClassName="h-auto max-h-48 rounded bg-white p-1 print:max-h-40"
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Answer key — on a new page when printing */}
          <div className="mt-8 print:mt-0" style={{ pageBreakBefore: 'always' }}>
            <h2 className="mb-3 text-lg font-semibold text-gray-800 dark:text-gray-200 print:text-black">
              Место для ответов
            </h2>
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr>
                  <th className="border border-gray-300 px-3 py-2 text-left font-medium text-gray-700 print:text-black">
                    №
                  </th>
                  <th className="border border-gray-300 px-3 py-2 text-left font-medium text-gray-700 print:text-black">
                    Ответ
                  </th>
                </tr>
              </thead>
              <tbody>
                {problems.map((_, idx) => (
                  <tr key={idx}>
                    <td className="border border-gray-300 px-3 py-2 text-gray-800 print:text-black w-16">
                      {idx + 1}
                    </td>
                    <td className="border border-gray-300 px-3 py-2 min-h-[2rem]">&nbsp;</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
