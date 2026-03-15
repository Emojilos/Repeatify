import { useEffect } from 'react'
import { useXpStore } from '../stores/xpStore'

export default function XpPopup() {
  const notifications = useXpStore((s) => s.notifications)

  return (
    <div className="pointer-events-none fixed right-6 top-4 z-50 flex flex-col items-end gap-2">
      {notifications.map((n) => (
        <XpBubble key={n.id} id={n.id} amount={n.amount} />
      ))}
    </div>
  )
}

function XpBubble({ id, amount }: { id: number; amount: number }) {
  const removeNotification = useXpStore((s) => s.removeNotification)

  useEffect(() => {
    const timer = setTimeout(() => removeNotification(id), 2500)
    return () => clearTimeout(timer)
  }, [id, removeNotification])

  return (
    <div className="animate-xp-popup rounded-lg bg-blue-600 px-4 py-2 text-sm font-bold text-white shadow-lg">
      +{amount} XP
    </div>
  )
}
