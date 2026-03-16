import { useParams, Link } from 'react-router-dom'

export default function PrototypeDetail() {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="mx-auto max-w-3xl p-6">
      <Link
        to="/topics"
        className="mb-4 inline-block text-sm text-blue-600 hover:underline dark:text-blue-400"
      >
        &larr; Все темы
      </Link>
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-800">
        <h1 className="mb-2 text-xl font-bold text-gray-900 dark:text-white">
          Прототип
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Страница прототипа {id} — в разработке.
        </p>
      </div>
    </div>
  )
}
