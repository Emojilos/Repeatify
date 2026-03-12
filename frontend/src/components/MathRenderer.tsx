import Markdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface MathRendererProps {
  content: string
}

export default function MathRenderer({ content }: MathRendererProps) {
  return (
    <div className="math-renderer prose prose-neutral max-w-none dark:prose-invert">
      <Markdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
        {content}
      </Markdown>
    </div>
  )
}
