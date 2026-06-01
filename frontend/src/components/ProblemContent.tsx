import MathRenderer from './MathRenderer'
import { proxyImageUrl } from '../lib/storage'

interface ProblemContentProps {
  text: string
  images?: string[] | null
  imageClassName?: string
}

type Segment =
  | { kind: 'text'; value: string }
  | { kind: 'image'; index: number; alt: string }

const PLACEHOLDER_RE = /(\{\{IMG:(\d+)\}\}|\[image:\s*([^\]]*)\])/g

/**
 * Renders problem text with inline images.
 *
 * If the text contains {{IMG:N}} or parser [image: ...] placeholders, images
 * are inserted inline at their correct positions. Otherwise falls back to
 * showing all images after the text (legacy format).
 *
 * Newlines in text are rendered as visual line breaks to separate а)/б) parts.
 */
export default function ProblemContent({ text, images, imageClassName = 'h-auto max-h-40 rounded bg-white p-1 dark:invert' }: ProblemContentProps) {
  const parsedLines = parseProblemText(text)
  const hasPlaceholders = parsedLines.some((line) => line.some((segment) => segment.kind === 'image'))
  const renderedImageIndexes = new Set<number>()

  if (hasPlaceholders && images && images.length > 0) {
    return (
      <div className="space-y-2">
        {parsedLines.map((line, lineIdx) => (
          <div key={lineIdx} className="leading-relaxed">
            {line.map((segment, i) => {
              if (segment.kind === 'image') {
                const url = images[segment.index]
                if (!url) return null
                renderedImageIndexes.add(segment.index)
                return (
                  <img
                    key={i}
                    src={proxyImageUrl(url)}
                    alt={segment.alt}
                    className={`mx-1 inline-block align-middle ${imageClassName}`}
                  />
                )
              }
              if (segment.value.trim()) {
                return <MathRenderer key={i} content={segment.value} inline />
              }
              return null
            })}
          </div>
        ))}
        {images.length > renderedImageIndexes.size && (
          <ImageList
            images={images.filter((_, index) => !renderedImageIndexes.has(index))}
            imageClassName={imageClassName}
          />
        )}
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
        {images && images.length > 0 && <ImageList images={images} imageClassName={imageClassName} />}
      </div>
    )
  }

  return (
    <div>
      <MathRenderer content={text} />
      {images && images.length > 0 && <ImageList images={images} imageClassName={imageClassName} />}
    </div>
  )
}

function parseProblemText(text: string): Segment[][] {
  let implicitImageIndex = 0
  return text.split('\n').filter(l => l.trim()).map((line) => {
    const segments: Segment[] = []
    let lastIndex = 0

    for (const match of line.matchAll(PLACEHOLDER_RE)) {
      if (match.index === undefined) continue
      if (match.index > lastIndex) {
        segments.push({ kind: 'text', value: line.slice(lastIndex, match.index) })
      }

      const explicitIndex = match[2] ? parseInt(match[2], 10) : null
      const alt = (match[3] || '').trim()
      const imageIndex = explicitIndex ?? implicitImageIndex
      implicitImageIndex = Math.max(implicitImageIndex, imageIndex + 1)
      segments.push({ kind: 'image', index: imageIndex, alt })
      lastIndex = match.index + match[0].length
    }

    if (lastIndex < line.length) {
      segments.push({ kind: 'text', value: line.slice(lastIndex) })
    }
    return segments
  })
}

function ImageList({ images, imageClassName }: { images: string[]; imageClassName: string }) {
  return (
    <div className="mt-3 flex flex-wrap gap-3">
      {images.map((url, i) => (
        <img key={`${url}-${i}`} src={proxyImageUrl(url)} alt="" className={imageClassName} />
      ))}
    </div>
  )
}
