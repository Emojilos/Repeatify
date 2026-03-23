import { useState } from 'react'

interface Timestamp {
  time: number
  label: string
}

interface YouTubePlayerProps {
  videoId: string
  timestamps?: Timestamp[]
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function YouTubePlayer({ videoId, timestamps }: YouTubePlayerProps) {
  const [startTime, setStartTime] = useState(0)
  const [activeTimestamp, setActiveTimestamp] = useState<number | null>(null)

  const seekTo = (time: number) => {
    setStartTime(time)
    setActiveTimestamp(time)
  }

  const src = `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1${startTime ? `&start=${startTime}` : ''}`

  return (
    <div className="w-full">
      <div className="relative w-full" style={{ paddingTop: '56.25%' }}>
        <iframe
          key={`${videoId}-${startTime}`}
          src={src}
          className="absolute inset-0 w-full h-full rounded-lg"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          title="YouTube video"
        />
      </div>

      {timestamps && timestamps.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {timestamps.map((ts) => (
            <button
              key={ts.time}
              onClick={() => seekTo(ts.time)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors ${
                activeTimestamp === ts.time
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
              }`}
            >
              <span className="font-mono text-xs opacity-70">
                {formatTime(ts.time)}
              </span>
              <span>{ts.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
