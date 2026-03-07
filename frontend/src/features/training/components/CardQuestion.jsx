import LatexRenderer from '../../../components/math/LatexRenderer.jsx'

export default function CardQuestion({ card }) {
  const { question_text, question_image_url, card_type } = card

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="text-[16px] leading-relaxed text-gray-800">
        <LatexRenderer text={question_text} />
      </div>

      {question_image_url && (
        <div className="mt-4 overflow-x-auto">
          <img
            src={question_image_url}
            alt="Иллюстрация к задаче"
            loading="lazy"
            className="max-w-full h-auto rounded-lg mx-auto block"
          />
        </div>
      )}

      {card_type === 'step_by_step' && (
        <p className="mt-3 text-sm text-gray-500">Задача с пошаговым решением</p>
      )}
    </div>
  )
}
