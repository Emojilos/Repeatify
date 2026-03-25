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
 */
export default function ProblemContent({ text, images, imageClassName = 'h-auto max-h-40 rounded bg-white p-1 dark:invert' }: ProblemContentProps) {
  const hasPlaceholders = /\{\{IMG:\d+\}\}/.test(text)

  if (hasPlaceholders && images && images.length > 0) {
    // Split text by {{IMG:N}} placeholders and interleave with images
    const parts = text.split(/(\{\{IMG:\d+\}\})/)
    return (
      <div>
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
  }

  // Legacy format: text + images below
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
