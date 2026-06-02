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
  text = normalizeTrigArtifacts(text)
  text = normalizeFractionArtifacts(text)
  text = normalizeSqrtArtifacts(text)
  text = text
    .replace(/π(?=[A-Za-zА-Яа-я])/g, '\\pi ')
    .replace(/π/g, '\\pi')

  return text.trim()
}

function normalizeLogArtifacts(value: string): string {
  return value
    .replace(/\blogx([+-])(\d)(?=\()/g, (_, sign: string, baseTail: string) => {
      return `\\log_{x${sign}${baseTail}}`
    })
    .replace(/\blogx([+-])(\d)(\d+)\b/g, (_, sign: string, baseTail: string, argument: string) => {
      return `\\log_{x${sign}${baseTail}} ${argument}`
    })
    .replace(/\blogx\s*\(/g, '\\log_x(')
    .replace(/\blogx\b/g, '\\log_x')
    .replace(/\blog([2-9])\s*\(/g, '\\log_$1(')
    .replace(/\blog([2-9])(?=√|\\sqrt)/g, '\\log_$1 ')
    .replace(/\blog([2-9])([0-9]+)\b/g, '\\log_$1 $2')
    .replace(/\blog([2-9])\s+([A-Za-zА-Яа-яπ])/g, '\\log_$1 $2')
}

function normalizeTrigArtifacts(value: string): string {
  return value
    .replace(/\bsin\b/g, '\\sin')
    .replace(/\bcos\b/g, '\\cos')
    .replace(/\btg\b/g, '\\operatorname{tg}')
    .replace(/\bctg\b/g, '\\operatorname{ctg}')
}

function normalizeFractionArtifacts(value: string): string {
  let text = value

  text = text.replace(
    /\(\s*\)\s*(\\log_[^\s]+)\s*(\\sin|\\cos|\\operatorname\{tg\}|\\operatorname\{ctg\})\s*π\s*=\s*(.+?)\.\s*(\d+)\s*$/g,
    (_, log: string, trig: string, rhs: string, denominator: string) => {
      return `${log}\\left(${trig}\\frac{\\pi}{${denominator}}\\right)=${rhs.trim()}`
    },
  )

  text = text.replace(
    /(\\sin|\\cos|\\operatorname\{tg\}|\\operatorname\{ctg\})\s*πx-?\s*=\s*(.+?)\.\s*(\d+)\s*$/g,
    (_, trig: string, rhs: string, denominator: string) => {
      return `${trig}\\frac{\\pi x}{${denominator}}=${rhs.trim()}`
    },
  )

  text = text.replace(
    /(\\sin|\\cos|\\operatorname\{tg\}|\\operatorname\{ctg\})\s*π\s*=\s*(.+?)\.\s*(\d+)\s*$/g,
    (_, trig: string, rhs: string, denominator: string) => {
      return `${trig}\\frac{\\pi}{${denominator}}=${rhs.trim()}`
    },
  )

  text = text.replace(
    /([=+\-*/(]\s*)(\d+)\.\s+(\d+)(?=\s*$|[),.;])/g,
    (_, prefix: string, numerator: string, denominator: string) => {
      return `${prefix}\\frac{${numerator}}{${denominator}}`
    },
  )

  return text
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
