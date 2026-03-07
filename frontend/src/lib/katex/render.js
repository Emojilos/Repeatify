import katex from 'katex'

export function renderLatex(text) {
  if (!text) return { parts: [{ type: 'text', content: '' }] }

  const parts = []
  // Match $$...$$ (block) or $...$ (inline)
  const regex = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g
  let lastIndex = 0
  let match

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }

    const raw = match[0]
    const isBlock = raw.startsWith('$$')
    const latex = isBlock ? raw.slice(2, -2) : raw.slice(1, -1)

    try {
      const html = katex.renderToString(latex, {
        displayMode: isBlock,
        throwOnError: true,
        trust: false,
        strict: 'warn',
      })
      parts.push({ type: isBlock ? 'block' : 'inline', content: html })
    } catch {
      parts.push({ type: 'text', content: raw })
    }

    lastIndex = match.index + raw.length
  }

  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.slice(lastIndex) })
  }

  return { parts }
}
