import { useToastStore } from '../stores/toastStore'

const typeStyles = {
  error: 'bg-red-600',
  success: 'bg-green-600',
  info: 'bg-blue-600',
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`${typeStyles[toast.type]} flex max-w-sm items-start gap-2 rounded-lg px-4 py-3 text-sm text-white shadow-lg`}
        >
          <span className="flex-1">{toast.message}</span>
          <button
            onClick={() => removeToast(toast.id)}
            className="ml-2 text-white/70 hover:text-white"
          >
            &times;
          </button>
        </div>
      ))}
    </div>
  )
}
