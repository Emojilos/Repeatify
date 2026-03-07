import 'katex/dist/katex.min.css'
import { renderLatex } from '../../lib/katex/render.js'

export default function LatexRenderer({ text }) {
  const { parts } = renderLatex(text)

  return (
    <span>
      {parts.map((part, i) => {
        if (part.type === 'text') {
          return <span key={i}>{part.content}</span>
        }
        if (part.type === 'block') {
          return (
            <div
              key={i}
              className="overflow-x-auto text-center my-2"
              dangerouslySetInnerHTML={{ __html: part.content }}
            />
          )
        }
        return (
          <span
            key={i}
            className="overflow-x-auto"
            dangerouslySetInnerHTML={{ __html: part.content }}
          />
        )
      })}
    </span>
  )
}
