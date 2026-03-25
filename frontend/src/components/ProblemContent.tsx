import MathRenderer from './MathRenderer'
import { proxyImageUrl } from '../lib/storage'

interface ProblemContentProps {
  text: string
  images?: string[] | null
  imageClassName?: string
}

/**
 * Renders problem text with inline images.
 *
 * If the text contains {{IMG:N}} placeholders, images are inserted inline
 * at their correct positions. Otherwise falls back to showing all images
 * after the text (legacy format).
 *
 * Newlines in text are rendered as visual line breaks to separate а)/б) parts.
 */
export default function ProblemContent({ text, images, imageClassName = 'h-auto max-h-40 rounded bg-white p-1 dark:invert' }: ProblemContentProps) {
  const hasPlaceholders = /\{\{IMG:\d+\}\}/.test(text)

  if (hasPlaceholders && images && images.length > 0) {
    // First split by newlines to create visual paragraphs
    const lines = text.split('\n').filter(l => l.trim())

    return (
      <div className="space-y-2">
        {lines.map((line, lineIdx) => {
          // Split each line by {{IMG:N}} placeholders and interleave with images
          const parts = line.split(/(\{\{IMG:\d+\}\})/)
          return (
            <div key={lineIdx}>
              {parts.map((part, i) => {
                const match = part.match(/^\{\{IMG:(\d+)\}\}$/)
                if (match) {
                  const imgIndex = parseInt(match[1], 10)
                  const url = images[imgIndex]
                  if (url) {
                    return (
                      <img
                        key={i}
                        src={proxyImageUrl(url)}
                        alt=""
                        className={imageClassName}
                        style={{ display: 'inline-block', verticalAlign: 'middle', margin: '4px 2px' }}
                      />
                    )
                  }
                  return null
                }
                if (part.trim()) {
                  return <MathRenderer key={i} content={part} />
                }
                return null
              })}
            </div>
          )
        })}
      </div>
    )
  }

  // Legacy or plain text: split by newlines for а)/б) separation
  const lines = text.split('\n').filter(l => l.trim())
  if (lines.length > 1) {
    return (
      <div className="space-y-2">
        {lines.map((line, i) => (
          <div key={i}>
            <MathRenderer content={line} />
          </div>
        ))}
        {images && images.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-3">
            {images.map((url, i) => (
              <img key={i} src={proxyImageUrl(url)} alt="" className={imageClassName} />
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      <MathRenderer content={text} />
      {images && images.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-3">
          {images.map((url, i) => (
            <img key={i} src={proxyImageUrl(url)} alt="" className={imageClassName} />
          ))}
        </div>
      )}
    </div>
  )
}
