import Markdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

const rehypeKatexOptions = {
  strict: false,
  throwOnError: false,
}

interface MathRendererProps {
  content: string
  inline?: boolean
}

export default function MathRenderer({ content, inline }: MathRendererProps) {
  const normalizedContent = normalizeMathMarkdown(content)

  if (inline) {
    return (
      <span className="math-renderer-inline prose prose-neutral max-w-none dark:prose-invert [&_p]:inline [&_p]:m-0">
        <Markdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[[rehypeKatex, rehypeKatexOptions]]}>
          {normalizedContent}
        </Markdown>
      </span>
    )
  }
  return (
    <div className="math-renderer prose prose-neutral max-w-none dark:prose-invert [&>:first-child]:mt-0">
      <Markdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[[rehypeKatex, rehypeKatexOptions]]}>
        {normalizedContent}
      </Markdown>
    </div>
  )
}

function normalizeMathMarkdown(content: string): string {
  return content.replace(
    /\$\$([\s\S]*?)\$\$|\$([^$]+?)\$/g,
    (match, displayMath: string | undefined, inlineMath: string | undefined) => {
      if (displayMath !== undefined) {
        return `$$${normalizeLatexFragment(displayMath)}$$`
      }
      if (inlineMath !== undefined) {
        return `$${normalizeLatexFragment(inlineMath)}$`
      }
      return match
    },
  )
}

function normalizeLatexFragment(value: string): string {
  let text = value
    .replace(/[−–]/g, '-')
    .replace(/\s+/g, ' ')

  text = normalizeLogArtifacts(text)
  text = normalizeSqrtArtifacts(text)

  return text.trim()
}

function normalizeLogArtifacts(value: string): string {
  return value
    .replace(/\blog([2-9])\s*\(/g, '\\log_$1(')
    .replace(/\blog([2-9])(?=√|\\sqrt)/g, '\\log_$1 ')
    .replace(/\blog([2-9])([0-9]+)\b/g, '\\log_$1 $2')
    .replace(/\blog([2-9])\s+([A-Za-zА-Яа-яπ])/g, '\\log_$1 $2')
}

function normalizeSqrtArtifacts(value: string): string {
  return value
    .replace(/√\s*-+\s*([^=]+?)\s*=/g, (_, radicand: string) => {
      return `\\sqrt{${normalizeRadicand(radicand)}}=`
    })
    .replace(/√\s*-+\s*([^,.;=]+)(?=[,.;]|$)/g, (_, radicand: string) => {
      return `\\sqrt{${normalizeRadicand(radicand)}}`
    })
    .replace(/√\s*(\([^)]*\)|[A-Za-zА-Яа-яπ][A-Za-zА-Яа-яπ0-9]*|\d+(?:[.,]\d+)?)/g, (_, radicand: string) => {
      return `\\sqrt{${normalizeRadicand(radicand)}}`
    })
}

function normalizeRadicand(value: string): string {
  return value
    .replace(/\s+/g, ' ')
    .replace(/\s*([+\-=])\s*/g, '$1')
    .trim()
}
