const RATINGS = [
  { value: 1, label: 'Снова', color: 'bg-[#DC2626] hover:bg-[#B91C1C]', shortLabel: '1' },
  { value: 2, label: 'Трудно', color: 'bg-[#F59E0B] hover:bg-[#D97706]', shortLabel: '2' },
  { value: 3, label: 'Хорошо', color: 'bg-[#16A34A] hover:bg-[#15803D]', shortLabel: '3' },
  { value: 4, label: 'Легко', color: 'bg-[#2563EB] hover:bg-[#1D4ED8]', shortLabel: '4' },
]

export default function RatingButtons({ onRate, disabled = true, maxRating = 4 }) {
  return (
    <div className="w-full max-w-2xl mx-auto grid grid-cols-4 gap-2">
      {RATINGS.map(({ value, label, color }) => {
        const isDisabledByMax = value > maxRating
        const isDisabled = disabled || isDisabledByMax

        return (
          <button
            key={value}
            onClick={() => onRate(value)}
            disabled={isDisabled}
            className={`
              py-3 px-2 rounded-lg text-white font-medium text-sm
              transition-colors duration-150
              ${isDisabled ? 'opacity-40 cursor-not-allowed' : color + ' cursor-pointer'}
              ${isDisabled ? 'bg-gray-400' : color}
            `}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
