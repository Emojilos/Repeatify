import Markdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface MathRendererProps {
  content: string
  inline?: boolean
}

export default function MathRenderer({ content, inline }: MathRendererProps) {
  if (inline) {
    return (
      <span className="math-renderer-inline prose prose-neutral max-w-none dark:prose-invert [&_p]:inline [&_p]:m-0">
        <Markdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
          {content}
        </Markdown>
      </span>
    )
  }
  return (
    <div className="math-renderer prose prose-neutral max-w-none dark:prose-invert">
      <Markdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
        {content}
      </Markdown>
    </div>
  )
}
