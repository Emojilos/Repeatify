import { useEffect, useRef, useCallback, useState } from 'react'

interface Timestamp {
  time: number
  label: string
}

interface YouTubePlayerProps {
  videoId: string
  timestamps?: Timestamp[]
}

declare global {
  interface Window {
    YT: typeof YT
    onYouTubeIframeAPIReady: (() => void) | undefined
  }
}

let apiLoadPromise: Promise<void> | null = null

function loadYouTubeAPI(): Promise<void> {
  if (window.YT?.Player) return Promise.resolve()
  if (apiLoadPromise) return apiLoadPromise

  apiLoadPromise = new Promise<void>((resolve) => {
    const existingCallback = window.onYouTubeIframeAPIReady
    window.onYouTubeIframeAPIReady = () => {
      existingCallback?.()
      resolve()
    }
    const script = document.createElement('script')
    script.src = 'https://www.youtube.com/iframe_api'
    document.head.appendChild(script)
  })

  return apiLoadPromise
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function YouTubePlayer({ videoId, timestamps }: YouTubePlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const playerRef = useRef<YT.Player | null>(null)
  const [activeTimestamp, setActiveTimestamp] = useState<number | null>(null)

  useEffect(() => {
    let destroyed = false

    loadYouTubeAPI().then(() => {
      if (destroyed || !containerRef.current) return

      // Clear previous player
      if (playerRef.current) {
        playerRef.current.destroy()
        playerRef.current = null
      }

      // Create a div for the player inside the container
      const playerDiv = document.createElement('div')
      containerRef.current.innerHTML = ''
      containerRef.current.appendChild(playerDiv)

      playerRef.current = new window.YT.Player(playerDiv, {
        videoId,
        width: '100%',
        height: '100%',
        playerVars: {
          rel: 0,
          modestbranding: 1,
          origin: window.location.origin,
        },
      })
    })

    return () => {
      destroyed = true
      if (playerRef.current) {
        playerRef.current.destroy()
        playerRef.current = null
      }
    }
  }, [videoId])

  const seekTo = useCallback((time: number) => {
    if (playerRef.current?.seekTo) {
      playerRef.current.seekTo(time, true)
      setActiveTimestamp(time)
    }
  }, [])

  return (
    <div className="w-full">
      <div className="relative w-full pt-[56.25%]">
        <div
          ref={containerRef}
          className="absolute inset-0 rounded-lg overflow-hidden [&>div]:w-full [&>div]:h-full [&>iframe]:w-full [&>iframe]:h-full"
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
