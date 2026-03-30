export interface FormulaSection {
  title: string
  formulas: string[] // Each string is a KaTeX formula line
}

export interface TaskFormulas {
  taskNumber: number
  title: string
  sections: FormulaSection[]
}

const allFormulas: TaskFormulas[] = [
  {
    taskNumber: 1,
    title: 'Планиметрия',
    sections: [
      {
        title: 'Прямоугольный треугольник',
        formulas: [
          'Теорема Пифагора: $a^2 + b^2 = c^2$',
          '$\\sin \\alpha = \\dfrac{a}{c}$, $\\cos \\alpha = \\dfrac{b}{c}$, $\\tg \\alpha = \\dfrac{a}{b}$',
          '$S = \\dfrac{1}{2} a b$ (произведение катетов)',
          'Медиана к гипотенузе $= \\dfrac{c}{2}$',
          'Сумма острых углов $= 90^\\circ$',
        ],
      },
      {
        title: 'Равнобедренный треугольник',
        formulas: [
          'Углы при основании равны',
          'Высота, биссектриса и медиана к основанию совпадают',
          'Высота к основанию делит его пополам',
          '$S = \\dfrac{1}{2} b^2 \\sin \\alpha$ (через боковую сторону и угол при вершине)',
        ],
      },
      {
        title: 'Треугольники: основные теоремы',
        formulas: [
          'Теорема косинусов: $c^2 = a^2 + b^2 - 2ab \\cos C$',
          'Теорема синусов: $\\dfrac{a}{\\sin A} = \\dfrac{b}{\\sin B} = \\dfrac{c}{\\sin C} = 2R$',
          'Сумма углов: $\\alpha + \\beta + \\gamma = 180^\\circ$',
          'Внешний угол = сумма двух внутренних, не смежных с ним',
          '$S = \\dfrac{1}{2} a h_a = \\dfrac{1}{2} ab \\sin C$',
          '$S = \\sqrt{p(p-a)(p-b)(p-c)}$ — формула Герона, $p = \\dfrac{a+b+c}{2}$',
        ],
      },
      {
        title: 'Площади фигур',
        formulas: [
          '$S_{\\text{прям}} = a \\cdot b$',
          '$S_{\\text{параллелогр}} = a \\cdot h = ab \\sin \\alpha$',
          '$S_{\\text{ромб}} = \\dfrac{d_1 \\cdot d_2}{2}$',
          '$S_{\\text{трапеция}} = \\dfrac{(a + b)}{2} \\cdot h$',
          '$S_{\\text{круг}} = \\pi r^2$, $C = 2\\pi r$',
          '$S_{\\text{сектор}} = \\dfrac{\\alpha}{360^\\circ} \\pi r^2 = \\dfrac{1}{2} l r$',
        ],
      },
      {
        title: 'Параллелограмм',
        formulas: [
          'Противоположные стороны равны и параллельны',
          'Диагонали делятся точкой пересечения пополам',
          'Сумма соседних углов $= 180^\\circ$',
          'Прямоугольник: $d^2 = a^2 + b^2$, диагонали равны',
          'Ромб: диагонали перпендикулярны, $S = \\dfrac{d_1 d_2}{2}$',
        ],
      },
      {
        title: 'Трапеция',
        formulas: [
          '$S = \\dfrac{a + b}{2} \\cdot h$',
          'Средняя линия $m = \\dfrac{a + b}{2}$, параллельна основаниям',
          'Равнобокая: боковые стороны равны, диагонали равны, можно вписать в окружность',
        ],
      },
      {
        title: 'Центральные и вписанные углы',
        formulas: [
          'Центральный угол = дуга',
          'Вписанный угол $= \\dfrac{1}{2}$ дуги',
          'Вписанный угол на диаметр $= 90^\\circ$',
          'Вписанные углы на одну дугу равны',
          'Угол между хордой и касательной $= \\dfrac{1}{2}$ дуги',
        ],
      },
      {
        title: 'Касательная, хорда, секущая',
        formulas: [
          'Касательная $\\perp$ радиусу в точке касания',
          'Два отрезка касательных из одной точки равны',
          '$|TA|^2 = |TB| \\cdot |TC|$ — касательная и секущая',
          '$PA \\cdot PB = PC \\cdot PD$ — пересекающиеся хорды',
        ],
      },
      {
        title: 'Вписанная окружность',
        formulas: [
          '$r = \\dfrac{S}{p}$, где $p$ — полупериметр',
          '$S = p \\cdot r$',
          'Прямоугольный треугольник: $r = \\dfrac{a + b - c}{2}$',
          'Четырёхугольник: можно вписать, если $a + c = b + d$',
        ],
      },
      {
        title: 'Описанная окружность',
        formulas: [
          '$R = \\dfrac{abc}{4S}$',
          '$\\dfrac{a}{\\sin A} = 2R$',
          'Прямоугольный треугольник: $R = \\dfrac{c}{2}$ (центр — середина гипотенузы)',
          'Четырёхугольник: можно описать, если $\\alpha + \\gamma = 180^\\circ$',
        ],
      },
    ],
  },
  {
    taskNumber: 2,
    title: 'Вычисления и преобразования',
    sections: [
      {
        title: 'Свойства степеней',
        formulas: [
          '$a^m \\cdot a^n = a^{m+n}$',
          '$\\dfrac{a^m}{a^n} = a^{m-n}$',
          '$(a^m)^n = a^{mn}$',
          '$(ab)^n = a^n b^n$',
          '$a^0 = 1$, $a^{-n} = \\dfrac{1}{a^n}$',
          '$a^{1/n} = \\sqrt[n]{a}$',
        ],
      },
      {
        title: 'Свойства корней',
        formulas: [
          '$\\sqrt[n]{ab} = \\sqrt[n]{a} \\cdot \\sqrt[n]{b}$',
          '$\\sqrt[n]{\\dfrac{a}{b}} = \\dfrac{\\sqrt[n]{a}}{\\sqrt[n]{b}}$',
          '$(\\sqrt[n]{a})^m = \\sqrt[n]{a^m} = a^{m/n}$',
        ],
      },
      {
        title: 'Свойства логарифмов',
        formulas: [
          '$\\log_a(xy) = \\log_a x + \\log_a y$',
          '$\\log_a\\dfrac{x}{y} = \\log_a x - \\log_a y$',
          '$\\log_a x^k = k \\cdot \\log_a x$',
          '$\\log_a b = \\dfrac{\\ln b}{\\ln a} = \\dfrac{\\log_c b}{\\log_c a}$ — формула перехода',
          '$\\log_a a = 1$, $\\log_a 1 = 0$',
          '$a^{\\log_a x} = x$',
          '$\\log_{a^k} b = \\dfrac{1}{k} \\log_a b$',
        ],
      },
      {
        title: 'Формулы сокращённого умножения',
        formulas: [
          '$(a \\pm b)^2 = a^2 \\pm 2ab + b^2$',
          '$(a - b)(a + b) = a^2 - b^2$',
          '$(a \\pm b)^3 = a^3 \\pm 3a^2b + 3ab^2 \\pm b^3$',
          '$a^3 \\pm b^3 = (a \\pm b)(a^2 \\mp ab + b^2)$',
        ],
      },
    ],
  },
  {
    taskNumber: 3,
    title: 'Простейшие уравнения',
    sections: [
      {
        title: 'Линейные и квадратные уравнения',
        formulas: [
          '$ax + b = 0 \\Rightarrow x = -\\dfrac{b}{a}$',
          '$ax^2 + bx + c = 0$: $D = b^2 - 4ac$, $x = \\dfrac{-b \\pm \\sqrt{D}}{2a}$',
          'Теорема Виета: $x_1 + x_2 = -\\dfrac{b}{a}$, $x_1 \\cdot x_2 = \\dfrac{c}{a}$',
        ],
      },
      {
        title: 'Показательные и логарифмические',
        formulas: [
          '$a^{f(x)} = a^{g(x)} \\Leftrightarrow f(x) = g(x)$ при $a > 0, a \\neq 1$',
          '$\\log_a f(x) = b \\Leftrightarrow f(x) = a^b$, $f(x) > 0$',
          '$\\log_a f(x) = \\log_a g(x) \\Leftrightarrow f(x) = g(x) > 0$',
        ],
      },
      {
        title: 'Иррациональные уравнения',
        formulas: [
          '$\\sqrt{f(x)} = g(x) \\Leftrightarrow \\begin{cases} f(x) = g^2(x) \\\\ g(x) \\geq 0 \\end{cases}$',
        ],
      },
    ],
  },
  {
    taskNumber: 4,
    title: 'Теория вероятностей',
    sections: [
      {
        title: 'Основные формулы',
        formulas: [
          '$P(A) = \\dfrac{m}{n}$ — классическое определение',
          '$P(A \\cup B) = P(A) + P(B) - P(A \\cap B)$',
          'Для несовместных событий: $P(A \\cup B) = P(A) + P(B)$',
          '$P(\\bar{A}) = 1 - P(A)$',
          'Для независимых событий: $P(A \\cap B) = P(A) \\cdot P(B)$',
        ],
      },
      {
        title: 'Условная вероятность',
        formulas: [
          '$P(A|B) = \\dfrac{P(A \\cap B)}{P(B)}$',
          'Формула полной вероятности: $P(A) = \\sum_{i} P(H_i) \\cdot P(A|H_i)$',
          'Формула Бернулли: $P_n(k) = C_n^k p^k (1-p)^{n-k}$',
        ],
      },
      {
        title: 'Комбинаторика',
        formulas: [
          '$C_n^k = \\dfrac{n!}{k!(n-k)!}$',
          '$A_n^k = \\dfrac{n!}{(n-k)!}$',
          '$P_n = n!$',
        ],
      },
    ],
  },
  {
    taskNumber: 5,
    title: 'Простейшие уравнения (повышенный)',
    sections: [
      {
        title: 'Тригонометрические уравнения',
        formulas: [
          '$\\sin x = a \\Rightarrow x = (-1)^n \\arcsin a + \\pi n,\\ n \\in \\mathbb{Z}$',
          '$\\cos x = a \\Rightarrow x = \\pm \\arccos a + 2\\pi n,\\ n \\in \\mathbb{Z}$',
          '$\\tan x = a \\Rightarrow x = \\arctan a + \\pi n,\\ n \\in \\mathbb{Z}$',
          '$\\sin x = 0 \\Rightarrow x = \\pi n$',
          '$\\cos x = 0 \\Rightarrow x = \\dfrac{\\pi}{2} + \\pi n$',
          '$\\sin x = 1 \\Rightarrow x = \\dfrac{\\pi}{2} + 2\\pi n$',
          '$\\cos x = 1 \\Rightarrow x = 2\\pi n$',
        ],
      },
      {
        title: 'Показательные и логарифмические',
        formulas: [
          '$a^{f(x)} = b \\Rightarrow f(x) = \\log_a b$',
          '$\\log_a f(x) = b \\Rightarrow f(x) = a^b$, $f(x) > 0$',
          'ОДЗ логарифма: основание $> 0$, $\\neq 1$; аргумент $> 0$',
        ],
      },
    ],
  },
  {
    taskNumber: 6,
    title: 'Планиметрия',
    sections: [
      {
        title: 'Подобие треугольников',
        formulas: [
          'Признаки подобия: по двум углам; по двум сторонам и углу; по трём сторонам',
          '$\\dfrac{S_1}{S_2} = k^2$, где $k$ — коэффициент подобия',
        ],
      },
      {
        title: 'Вписанные и описанные окружности',
        formulas: [
          '$r = \\dfrac{S}{p}$ — радиус вписанной окружности',
          '$R = \\dfrac{abc}{4S}$ — радиус описанной окружности',
          'Около четырёхугольника можно описать окружность $\\Leftrightarrow$ сумма противоположных углов $= 180^\\circ$',
          'В четырёхугольник можно вписать окружность $\\Leftrightarrow$ суммы противоположных сторон равны',
        ],
      },
      {
        title: 'Средняя линия',
        formulas: [
          'Средняя линия треугольника параллельна основанию и равна его половине',
          'Средняя линия трапеции: $m = \\dfrac{a+b}{2}$',
        ],
      },
    ],
  },
  {
    taskNumber: 7,
    title: 'Производная и первообразная',
    sections: [
      {
        title: 'Таблица производных',
        formulas: [
          '$(C)\' = 0$',
          '$(x^n)\' = nx^{n-1}$',
          '$(\\sin x)\' = \\cos x$',
          '$(\\cos x)\' = -\\sin x$',
          '$(\\tan x)\' = \\dfrac{1}{\\cos^2 x}$',
          '$(e^x)\' = e^x$',
          '$(a^x)\' = a^x \\ln a$',
          '$(\\ln x)\' = \\dfrac{1}{x}$',
          '$(\\log_a x)\' = \\dfrac{1}{x \\ln a}$',
          '$(\\sqrt{x})\' = \\dfrac{1}{2\\sqrt{x}}$',
        ],
      },
      {
        title: 'Правила дифференцирования',
        formulas: [
          '$(f \\pm g)\' = f\' \\pm g\'$',
          '$(f \\cdot g)\' = f\' g + f g\'$',
          '$\\left(\\dfrac{f}{g}\\right)\' = \\dfrac{f\' g - f g\'}{g^2}$',
          '$(f(g(x)))\' = f\'(g(x)) \\cdot g\'(x)$ — цепное правило',
          '$(Cf)\' = C \\cdot f\'$',
        ],
      },
      {
        title: 'Таблица первообразных',
        formulas: [
          '$\\int x^n\\,dx = \\dfrac{x^{n+1}}{n+1} + C$, $n \\neq -1$',
          '$\\int \\dfrac{1}{x}\\,dx = \\ln|x| + C$',
          '$\\int e^x\\,dx = e^x + C$',
          '$\\int a^x\\,dx = \\dfrac{a^x}{\\ln a} + C$',
          '$\\int \\sin x\\,dx = -\\cos x + C$',
          '$\\int \\cos x\\,dx = \\sin x + C$',
          '$\\int \\dfrac{1}{\\cos^2 x}\\,dx = \\tan x + C$',
        ],
      },
      {
        title: 'Применение производной',
        formulas: [
          '$f\'(x_0) = 0$ — необходимое условие экстремума',
          '$f\'(x_0) = k_{\\text{касат}}$ — угловой коэффициент касательной',
          'Уравнение касательной: $y = f(x_0) + f\'(x_0)(x - x_0)$',
          'Функция возрастает при $f\'(x) > 0$, убывает при $f\'(x) < 0$',
        ],
      },
    ],
  },
  {
    taskNumber: 8,
    title: 'Стереометрия (вычисления)',
    sections: [
      {
        title: 'Объёмы тел',
        formulas: [
          '$V_{\\text{призма}} = S_{\\text{осн}} \\cdot h$',
          '$V_{\\text{пирамида}} = \\dfrac{1}{3} S_{\\text{осн}} \\cdot h$',
          '$V_{\\text{цилиндр}} = \\pi r^2 h$',
          '$V_{\\text{конус}} = \\dfrac{1}{3} \\pi r^2 h$',
          '$V_{\\text{шар}} = \\dfrac{4}{3} \\pi r^3$',
          '$V_{\\text{ус. конус}} = \\dfrac{\\pi h}{3}(R^2 + Rr + r^2)$',
        ],
      },
      {
        title: 'Площади поверхностей',
        formulas: [
          '$S_{\\text{бок. цил}} = 2\\pi r h$, $S_{\\text{полн}} = 2\\pi r(r + h)$',
          '$S_{\\text{бок. конус}} = \\pi r l$, $l = \\sqrt{r^2 + h^2}$',
          '$S_{\\text{шар}} = 4\\pi r^2$',
        ],
      },
    ],
  },
  {
    taskNumber: 9,
    title: 'Вычисления и преобразования (повышенный)',
    sections: [
      {
        title: 'Тригонометрия: основные тождества',
        formulas: [
          '$\\sin^2 x + \\cos^2 x = 1$',
          '$\\tan x = \\dfrac{\\sin x}{\\cos x}$, $\\cot x = \\dfrac{\\cos x}{\\sin x}$',
          '$1 + \\tan^2 x = \\dfrac{1}{\\cos^2 x}$',
          '$1 + \\cot^2 x = \\dfrac{1}{\\sin^2 x}$',
        ],
      },
      {
        title: 'Формулы сложения',
        formulas: [
          '$\\sin(\\alpha \\pm \\beta) = \\sin\\alpha\\cos\\beta \\pm \\cos\\alpha\\sin\\beta$',
          '$\\cos(\\alpha \\pm \\beta) = \\cos\\alpha\\cos\\beta \\mp \\sin\\alpha\\sin\\beta$',
          '$\\tan(\\alpha \\pm \\beta) = \\dfrac{\\tan\\alpha \\pm \\tan\\beta}{1 \\mp \\tan\\alpha\\tan\\beta}$',
        ],
      },
      {
        title: 'Формулы двойного угла',
        formulas: [
          '$\\sin 2\\alpha = 2\\sin\\alpha\\cos\\alpha$',
          '$\\cos 2\\alpha = \\cos^2\\alpha - \\sin^2\\alpha = 2\\cos^2\\alpha - 1 = 1 - 2\\sin^2\\alpha$',
          '$\\tan 2\\alpha = \\dfrac{2\\tan\\alpha}{1 - \\tan^2\\alpha}$',
        ],
      },
      {
        title: 'Формулы понижения степени',
        formulas: [
          '$\\sin^2\\alpha = \\dfrac{1 - \\cos 2\\alpha}{2}$',
          '$\\cos^2\\alpha = \\dfrac{1 + \\cos 2\\alpha}{2}$',
        ],
      },
      {
        title: 'Формулы приведения',
        formulas: [
          '$\\sin(\\pi - x) = \\sin x$, $\\cos(\\pi - x) = -\\cos x$',
          '$\\sin(\\pi + x) = -\\sin x$, $\\cos(\\pi + x) = -\\cos x$',
          '$\\sin\\left(\\dfrac{\\pi}{2} - x\\right) = \\cos x$, $\\cos\\left(\\dfrac{\\pi}{2} - x\\right) = \\sin x$',
          '$\\sin\\left(\\dfrac{\\pi}{2} + x\\right) = \\cos x$, $\\cos\\left(\\dfrac{\\pi}{2} + x\\right) = -\\sin x$',
        ],
      },
      {
        title: 'Сумма и разность тригонометрических функций',
        formulas: [
          '$\\sin\\alpha + \\sin\\beta = 2\\sin\\dfrac{\\alpha+\\beta}{2}\\cos\\dfrac{\\alpha-\\beta}{2}$',
          '$\\sin\\alpha - \\sin\\beta = 2\\cos\\dfrac{\\alpha+\\beta}{2}\\sin\\dfrac{\\alpha-\\beta}{2}$',
          '$\\cos\\alpha + \\cos\\beta = 2\\cos\\dfrac{\\alpha+\\beta}{2}\\cos\\dfrac{\\alpha-\\beta}{2}$',
          '$\\cos\\alpha - \\cos\\beta = -2\\sin\\dfrac{\\alpha+\\beta}{2}\\sin\\dfrac{\\alpha-\\beta}{2}$',
        ],
      },
      {
        title: 'Произведение тригонометрических функций',
        formulas: [
          '$\\sin\\alpha\\cos\\beta = \\dfrac{1}{2}[\\sin(\\alpha+\\beta) + \\sin(\\alpha-\\beta)]$',
          '$\\cos\\alpha\\cos\\beta = \\dfrac{1}{2}[\\cos(\\alpha-\\beta) + \\cos(\\alpha+\\beta)]$',
          '$\\sin\\alpha\\sin\\beta = \\dfrac{1}{2}[\\cos(\\alpha-\\beta) - \\cos(\\alpha+\\beta)]$',
        ],
      },
    ],
  },
  {
    taskNumber: 10,
    title: 'Задачи с прикладным содержанием',
    sections: [
      {
        title: 'Основные формулы',
        formulas: [
          '$S = v \\cdot t$ — путь = скорость $\\times$ время',
          '$A = P \\cdot t$ — работа = производительность $\\times$ время',
          '$F = k \\cdot x$ — закон Гука',
          '$T = T_0 + \\Delta T$ — изменение температуры',
          'Процент: $\\dfrac{\\text{часть}}{\\text{целое}} \\cdot 100\\%$',
          'Единицы: $1$ км $= 1000$ м, $1$ ч $= 60$ мин $= 3600$ с',
        ],
      },
    ],
  },
  {
    taskNumber: 11,
    title: 'Текстовые задачи',
    sections: [
      {
        title: 'Задачи на движение',
        formulas: [
          '$S = v \\cdot t$, $v = \\dfrac{S}{t}$, $t = \\dfrac{S}{v}$',
          'Навстречу: $v_{\\text{сближ}} = v_1 + v_2$',
          'Вдогонку: $v_{\\text{удал}} = v_1 - v_2$',
          'По течению: $v = v_{\\text{собств}} + v_{\\text{теч}}$',
          'Против течения: $v = v_{\\text{собств}} - v_{\\text{теч}}$',
        ],
      },
      {
        title: 'Задачи на работу',
        formulas: [
          '$A = p \\cdot t$, $p = \\dfrac{A}{t}$',
          'Совместная работа: $\\dfrac{1}{t} = \\dfrac{1}{t_1} + \\dfrac{1}{t_2}$',
        ],
      },
      {
        title: 'Задачи на смеси и сплавы',
        formulas: [
          '$\\text{масса вещества} = \\text{концентрация} \\times \\text{масса раствора}$',
          '$c = \\dfrac{m_{\\text{вещ}}}{m_{\\text{раствора}}} \\cdot 100\\%$',
        ],
      },
      {
        title: 'Задачи на проценты',
        formulas: [
          'Увеличение на $p\\%$: $x \\cdot (1 + \\dfrac{p}{100})$',
          'Уменьшение на $p\\%$: $x \\cdot (1 - \\dfrac{p}{100})$',
          '$n$ раз увеличение на $p\\%$: $x \\cdot (1 + \\dfrac{p}{100})^n$',
        ],
      },
    ],
  },
  {
    taskNumber: 12,
    title: 'Наибольшее и наименьшее значение функций',
    sections: [
      {
        title: 'Алгоритм нахождения экстремумов',
        formulas: [
          '1. Найти $f\'(x)$ и приравнять к нулю',
          '2. Определить знак $f\'(x)$ на интервалах',
          '3. $f\'$ меняет знак с $+$ на $-$ $\\Rightarrow$ максимум',
          '4. $f\'$ меняет знак с $-$ на $+$ $\\Rightarrow$ минимум',
        ],
      },
      {
        title: 'На отрезке $[a, b]$',
        formulas: [
          '1. Найти $f\'(x) = 0$ — стационарные точки на $[a, b]$',
          '2. Вычислить $f$ в стационарных точках и на концах: $f(a)$, $f(b)$',
          '3. Выбрать наибольшее/наименьшее значение',
        ],
      },
      {
        title: 'Вторая производная',
        formulas: [
          '$f\'\'(x_0) > 0 \\Rightarrow$ минимум, $f\'\'(x_0) < 0 \\Rightarrow$ максимум',
          'Точки перегиба: $f\'\'(x_0) = 0$ и $f\'\'$ меняет знак',
        ],
      },
    ],
  },
  {
    taskNumber: 13,
    title: 'Уравнения',
    sections: [
      {
        title: 'Тригонометрические уравнения',
        formulas: [
          '$\\sin x = a \\Rightarrow x = (-1)^n \\arcsin a + \\pi n,\\ n \\in \\mathbb{Z}$',
          '$\\cos x = a \\Rightarrow x = \\pm \\arccos a + 2\\pi n,\\ n \\in \\mathbb{Z}$',
          '$\\tan x = a \\Rightarrow x = \\arctan a + \\pi n,\\ n \\in \\mathbb{Z}$',
          '$\\cot x = a \\Rightarrow x = \\text{arccot}\\, a + \\pi n,\\ n \\in \\mathbb{Z}$',
        ],
      },
      {
        title: 'Частные случаи',
        formulas: [
          '$\\sin x = 0 \\Rightarrow x = \\pi n$',
          '$\\sin x = 1 \\Rightarrow x = \\dfrac{\\pi}{2} + 2\\pi n$',
          '$\\sin x = -1 \\Rightarrow x = -\\dfrac{\\pi}{2} + 2\\pi n$',
          '$\\cos x = 0 \\Rightarrow x = \\dfrac{\\pi}{2} + \\pi n$',
          '$\\cos x = 1 \\Rightarrow x = 2\\pi n$',
          '$\\cos x = -1 \\Rightarrow x = \\pi + 2\\pi n$',
        ],
      },
      {
        title: 'Основное тригонометрическое тождество',
        formulas: [
          '$\\sin^2 x + \\cos^2 x = 1$',
          '$\\tan x = \\dfrac{\\sin x}{\\cos x}$, $\\cot x = \\dfrac{\\cos x}{\\sin x}$',
          '$\\tan x \\cdot \\cot x = 1$',
          '$1 + \\tan^2 x = \\dfrac{1}{\\cos^2 x}$',
          '$1 + \\cot^2 x = \\dfrac{1}{\\sin^2 x}$',
        ],
      },
      {
        title: 'Формулы двойного угла',
        formulas: [
          '$\\sin 2\\alpha = 2\\sin\\alpha\\cos\\alpha$',
          '$\\cos 2\\alpha = \\cos^2\\alpha - \\sin^2\\alpha = 2\\cos^2\\alpha - 1 = 1 - 2\\sin^2\\alpha$',
          '$\\tan 2\\alpha = \\dfrac{2\\tan\\alpha}{1 - \\tan^2\\alpha}$',
        ],
      },
      {
        title: 'Формулы тройного угла',
        formulas: [
          '$\\sin 3\\alpha = 3\\sin\\alpha - 4\\sin^3\\alpha$',
          '$\\cos 3\\alpha = 4\\cos^3\\alpha - 3\\cos\\alpha$',
        ],
      },
      {
        title: 'Формулы половинного угла',
        formulas: [
          '$\\sin\\dfrac{\\alpha}{2} = \\pm\\sqrt{\\dfrac{1 - \\cos\\alpha}{2}}$',
          '$\\cos\\dfrac{\\alpha}{2} = \\pm\\sqrt{\\dfrac{1 + \\cos\\alpha}{2}}$',
          '$\\tan\\dfrac{\\alpha}{2} = \\dfrac{\\sin\\alpha}{1 + \\cos\\alpha} = \\dfrac{1 - \\cos\\alpha}{\\sin\\alpha}$',
        ],
      },
      {
        title: 'Формулы сложения',
        formulas: [
          '$\\sin(\\alpha \\pm \\beta) = \\sin\\alpha\\cos\\beta \\pm \\cos\\alpha\\sin\\beta$',
          '$\\cos(\\alpha \\pm \\beta) = \\cos\\alpha\\cos\\beta \\mp \\sin\\alpha\\sin\\beta$',
          '$\\tan(\\alpha \\pm \\beta) = \\dfrac{\\tan\\alpha \\pm \\tan\\beta}{1 \\mp \\tan\\alpha\\tan\\beta}$',
        ],
      },
      {
        title: 'Сумма и разность',
        formulas: [
          '$\\sin\\alpha + \\sin\\beta = 2\\sin\\dfrac{\\alpha+\\beta}{2}\\cos\\dfrac{\\alpha-\\beta}{2}$',
          '$\\sin\\alpha - \\sin\\beta = 2\\cos\\dfrac{\\alpha+\\beta}{2}\\sin\\dfrac{\\alpha-\\beta}{2}$',
          '$\\cos\\alpha + \\cos\\beta = 2\\cos\\dfrac{\\alpha+\\beta}{2}\\cos\\dfrac{\\alpha-\\beta}{2}$',
          '$\\cos\\alpha - \\cos\\beta = -2\\sin\\dfrac{\\alpha+\\beta}{2}\\sin\\dfrac{\\alpha-\\beta}{2}$',
        ],
      },
      {
        title: 'Произведение',
        formulas: [
          '$\\sin\\alpha\\cos\\beta = \\dfrac{1}{2}[\\sin(\\alpha+\\beta) + \\sin(\\alpha-\\beta)]$',
          '$\\cos\\alpha\\cos\\beta = \\dfrac{1}{2}[\\cos(\\alpha-\\beta) + \\cos(\\alpha+\\beta)]$',
          '$\\sin\\alpha\\sin\\beta = \\dfrac{1}{2}[\\cos(\\alpha-\\beta) - \\cos(\\alpha+\\beta)]$',
        ],
      },
      {
        title: 'Формулы понижения степени',
        formulas: [
          '$\\sin^2\\alpha = \\dfrac{1 - \\cos 2\\alpha}{2}$',
          '$\\cos^2\\alpha = \\dfrac{1 + \\cos 2\\alpha}{2}$',
        ],
      },
      {
        title: 'Формулы приведения',
        formulas: [
          '$\\sin(\\pi - x) = \\sin x$, $\\cos(\\pi - x) = -\\cos x$',
          '$\\sin(\\pi + x) = -\\sin x$, $\\cos(\\pi + x) = -\\cos x$',
          '$\\sin\\left(\\dfrac{\\pi}{2} - x\\right) = \\cos x$, $\\cos\\left(\\dfrac{\\pi}{2} - x\\right) = \\sin x$',
          '$\\sin\\left(\\dfrac{\\pi}{2} + x\\right) = \\cos x$, $\\cos\\left(\\dfrac{\\pi}{2} + x\\right) = -\\sin x$',
        ],
      },
      {
        title: 'Вспомогательный угол (метод)',
        formulas: [
          '$a\\sin x + b\\cos x = \\sqrt{a^2+b^2} \\sin(x + \\varphi)$, где $\\tan\\varphi = \\dfrac{b}{a}$',
        ],
      },
      {
        title: 'Значения тригонометрических функций',
        formulas: [
          '$\\sin 0 = 0$, $\\sin\\dfrac{\\pi}{6} = \\dfrac{1}{2}$, $\\sin\\dfrac{\\pi}{4} = \\dfrac{\\sqrt{2}}{2}$, $\\sin\\dfrac{\\pi}{3} = \\dfrac{\\sqrt{3}}{2}$, $\\sin\\dfrac{\\pi}{2} = 1$',
          '$\\cos 0 = 1$, $\\cos\\dfrac{\\pi}{6} = \\dfrac{\\sqrt{3}}{2}$, $\\cos\\dfrac{\\pi}{4} = \\dfrac{\\sqrt{2}}{2}$, $\\cos\\dfrac{\\pi}{3} = \\dfrac{1}{2}$, $\\cos\\dfrac{\\pi}{2} = 0$',
          '$\\tan 0 = 0$, $\\tan\\dfrac{\\pi}{6} = \\dfrac{\\sqrt{3}}{3}$, $\\tan\\dfrac{\\pi}{4} = 1$, $\\tan\\dfrac{\\pi}{3} = \\sqrt{3}$',
        ],
      },
    ],
  },
  {
    taskNumber: 14,
    title: 'Стереометрия',
    sections: [
      {
        title: 'Координатный метод',
        formulas: [
          'Расстояние: $d = \\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2 + (z_2-z_1)^2}$',
          'Середина отрезка: $M\\left(\\dfrac{x_1+x_2}{2},\\dfrac{y_1+y_2}{2},\\dfrac{z_1+z_2}{2}\\right)$',
          'Длина вектора: $|\\vec{a}| = \\sqrt{a_x^2 + a_y^2 + a_z^2}$',
        ],
      },
      {
        title: 'Скалярное и векторное произведение',
        formulas: [
          '$\\vec{a} \\cdot \\vec{b} = a_x b_x + a_y b_y + a_z b_z = |\\vec{a}||\\vec{b}|\\cos\\alpha$',
          '$\\cos\\alpha = \\dfrac{\\vec{a} \\cdot \\vec{b}}{|\\vec{a}| \\cdot |\\vec{b}|}$',
          '$\\vec{a} \\times \\vec{b} = \\begin{vmatrix} \\vec{i} & \\vec{j} & \\vec{k} \\\\ a_x & a_y & a_z \\\\ b_x & b_y & b_z \\end{vmatrix}$',
          '$|\\vec{a} \\times \\vec{b}| = |\\vec{a}||\\vec{b}|\\sin\\alpha$ — площадь параллелограмма',
        ],
      },
      {
        title: 'Уравнение плоскости и расстояния',
        formulas: [
          'Уравнение плоскости: $Ax + By + Cz + D = 0$, нормаль $\\vec{n} = (A, B, C)$',
          'Расстояние от точки $(x_0,y_0,z_0)$ до плоскости: $d = \\dfrac{|Ax_0+By_0+Cz_0+D|}{\\sqrt{A^2+B^2+C^2}}$',
          'Расстояние между скрещ. прямыми: $d = \\dfrac{|\\vec{AB} \\cdot (\\vec{u} \\times \\vec{v})|}{|\\vec{u} \\times \\vec{v}|}$',
        ],
      },
      {
        title: 'Углы',
        formulas: [
          'Угол между прямыми: $\\cos\\alpha = \\dfrac{|\\vec{a} \\cdot \\vec{b}|}{|\\vec{a}| \\cdot |\\vec{b}|}$',
          'Угол между прямой и плоскостью: $\\sin\\alpha = \\dfrac{|\\vec{l} \\cdot \\vec{n}|}{|\\vec{l}| \\cdot |\\vec{n}|}$',
          'Угол между плоскостями: $\\cos\\alpha = \\dfrac{|\\vec{n_1} \\cdot \\vec{n_2}|}{|\\vec{n_1}| \\cdot |\\vec{n_2}|}$',
          'Двугранный угол — угол между перпендикулярами к ребру в обеих гранях',
        ],
      },
      {
        title: 'Объёмы и площади',
        formulas: [
          '$V_{\\text{призма}} = S_{\\text{осн}} \\cdot h$',
          '$V_{\\text{пирамида}} = \\dfrac{1}{3} S_{\\text{осн}} \\cdot h$',
          '$V_{\\text{тетраэдр}} = \\dfrac{1}{6}|\\vec{a} \\cdot (\\vec{b} \\times \\vec{c})|$',
          '$S_{\\triangle} = \\dfrac{1}{2}|\\vec{a} \\times \\vec{b}|$',
        ],
      },
      {
        title: 'Теоремы',
        formulas: [
          'Теорема о трёх перпендикулярах',
          'Прямая перпендикулярна плоскости $\\Leftrightarrow$ перпендикулярна двум пересекающимся прямым в ней',
          'Параллельные плоскости: если две пересекающиеся прямые одной плоскости параллельны другой плоскости',
        ],
      },
    ],
  },
  {
    taskNumber: 15,
    title: 'Неравенства',
    sections: [
      {
        title: 'Метод интервалов',
        formulas: [
          '1. Перенести всё в одну сторону: $f(x) > 0$',
          '2. Найти нули: $f(x) = 0$',
          '3. Отметить на числовой прямой, определить знаки',
          '4. Выписать ответ',
        ],
      },
      {
        title: 'Показательные неравенства',
        formulas: [
          '$a^{f(x)} > a^{g(x)}$: при $a > 1 \\Rightarrow f(x) > g(x)$; при $0 < a < 1 \\Rightarrow f(x) < g(x)$',
        ],
      },
      {
        title: 'Логарифмические неравенства',
        formulas: [
          '$\\log_a f(x) > \\log_a g(x)$:',
          'При $a > 1$: $\\begin{cases} f(x) > g(x) \\\\ g(x) > 0 \\end{cases}$',
          'При $0 < a < 1$: $\\begin{cases} f(x) < g(x) \\\\ f(x) > 0 \\end{cases}$',
          'ОДЗ: аргумент $> 0$, основание $> 0$ и $\\neq 1$',
        ],
      },
      {
        title: 'Метод рационализации',
        formulas: [
          '$\\log_{h(x)} f(x) > \\log_{h(x)} g(x) \\Leftrightarrow (h(x) - 1)(f(x) - g(x)) > 0$ при $f, g, h > 0$, $h \\neq 1$',
        ],
      },
    ],
  },
  {
    taskNumber: 16,
    title: 'Экономическая задача',
    sections: [
      {
        title: 'Простые и сложные проценты',
        formulas: [
          'Простые проценты: $S = S_0(1 + n \\cdot r)$',
          'Сложные проценты: $S = S_0(1 + r)^n$',
          '$r$ — процентная ставка, $n$ — число периодов',
        ],
      },
      {
        title: 'Кредиты',
        formulas: [
          'Аннуитетный платёж: $x = S \\cdot \\dfrac{r(1+r)^n}{(1+r)^n - 1}$',
          'Дифференцированный платёж: $P_k = \\dfrac{S}{n} + \\left(S - \\dfrac{S(k-1)}{n}\\right) \\cdot r$',
          'Общая сумма: $\\sum P_k$ — сумма всех платежей',
          'Переплата = сумма всех платежей $- S$',
        ],
      },
      {
        title: 'Вклады',
        formulas: [
          'Через $n$ лет: $S_n = S_0 (1 + r)^n$',
          'С ежегодным пополнением $d$: $S_n = S_0(1+r)^n + d \\cdot \\dfrac{(1+r)^n - 1}{r}$',
        ],
      },
    ],
  },
  {
    taskNumber: 17,
    title: 'Планиметрия (часть 2)',
    sections: [
      {
        title: 'Площади и длины',
        formulas: [
          '$S_{\\triangle} = \\dfrac{1}{2}ab\\sin C$',
          '$S_{\\triangle} = \\dfrac{abc}{4R} = pr$',
          '$S_{\\triangle} = \\sqrt{p(p-a)(p-b)(p-c)}$',
          'Медиана: $m_a = \\dfrac{1}{2}\\sqrt{2b^2 + 2c^2 - a^2}$',
          'Биссектриса: $l_a = \\dfrac{2bc\\cos\\frac{A}{2}}{b+c}$',
        ],
      },
      {
        title: 'Окружности',
        formulas: [
          'Степень точки: $PA \\cdot PB = PC \\cdot PD$',
          'Касательная и секущая: $PT^2 = PA \\cdot PB$',
          'Вписанный угол = $\\dfrac{1}{2}$ дуги, на которую опирается',
          'Угол между хордами: $\\angle = \\dfrac{1}{2}(\\smile_1 + \\smile_2)$',
        ],
      },
      {
        title: 'Координатный метод',
        formulas: [
          'Расстояние: $d = \\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}$',
          'Уравнение прямой: $ax + by + c = 0$',
          'Расстояние от точки до прямой: $d = \\dfrac{|ax_0 + by_0 + c|}{\\sqrt{a^2+b^2}}$',
          'Уравнение окружности: $(x-a)^2 + (y-b)^2 = r^2$',
        ],
      },
      {
        title: 'Подобие',
        formulas: [
          'Коэффициент подобия $k$: стороны $\\sim k$, площади $\\sim k^2$',
          'Признаки подобия: AA, SAS, SSS',
        ],
      },
    ],
  },
  {
    taskNumber: 18,
    title: 'Задача с параметром',
    sections: [
      {
        title: 'Основные методы',
        formulas: [
          'Аналитический метод: решить как обычное уравнение, затем исследовать по параметру',
          'Графический метод: построить графики $y = f(x)$ и $y = g(x, a)$',
          'Метод областей: разбить плоскость $(x, a)$ на области',
        ],
      },
      {
        title: 'Квадратный трёхчлен $f(x) = ax^2+bx+c$',
        formulas: [
          '$D = b^2 - 4ac$',
          'Вершина параболы: $x_0 = -\\dfrac{b}{2a}$, $y_0 = -\\dfrac{D}{4a}$',
          '$f(x) > 0$ для всех $x$: $\\begin{cases} a > 0 \\\\ D < 0 \\end{cases}$',
          'Расположение корней: теорема о промежуточном значении',
        ],
      },
      {
        title: 'Полезные неравенства',
        formulas: [
          '$|a| \\geq 0$, $|a+b| \\leq |a| + |b|$',
          '$a^2 + b^2 \\geq 2ab$ (неравенство о средних)',
          '$\\dfrac{a+b}{2} \\geq \\sqrt{ab}$ для $a, b \\geq 0$ (AM-GM)',
          '$|f(x)| = g(x) \\Leftrightarrow f(x) = \\pm g(x),\\ g(x) \\geq 0$',
        ],
      },
    ],
  },
  {
    taskNumber: 19,
    title: 'Теория чисел',
    sections: [
      {
        title: 'Делимость',
        formulas: [
          '$a | b \\Leftrightarrow b = ak$ для некоторого $k \\in \\mathbb{Z}$',
          'Признаки делимости: на 2 (чётная последняя цифра), на 3 (сумма цифр $\\vdots 3$), на 9 (сумма цифр $\\vdots 9$)',
          'НОД и НОК: $\\text{НОД}(a,b) \\cdot \\text{НОК}(a,b) = a \\cdot b$',
          'Алгоритм Евклида: $\\gcd(a, b) = \\gcd(b, a \\mod b)$',
        ],
      },
      {
        title: 'Остатки',
        formulas: [
          '$a \\equiv b \\pmod{m} \\Leftrightarrow m | (a - b)$',
          '$(a + b) \\mod m = ((a \\mod m) + (b \\mod m)) \\mod m$',
          '$(a \\cdot b) \\mod m = ((a \\mod m) \\cdot (b \\mod m)) \\mod m$',
        ],
      },
      {
        title: 'Полезные факты',
        formulas: [
          'Чётное $\\pm$ чётное $=$ чётное, нечётное $\\pm$ нечётное $=$ чётное',
          'Чётное $\\times$ любое $=$ чётное',
          'Нечётное $\\times$ нечётное $=$ нечётное',
          'Квадрат чётного $\\vdots 4$, квадрат нечётного даёт остаток 1 при делении на 4',
          'Основная теорема арифметики: каждое натуральное число $> 1$ единственным образом разлагается на простые',
        ],
      },
      {
        title: 'Последовательности',
        formulas: [
          'Арифм. прогрессия: $a_n = a_1 + (n-1)d$, $S_n = \\dfrac{(a_1+a_n)n}{2}$',
          'Геом. прогрессия: $b_n = b_1 q^{n-1}$, $S_n = \\dfrac{b_1(q^n - 1)}{q - 1}$',
          'Сумма первых $n$ натуральных: $\\dfrac{n(n+1)}{2}$',
          'Сумма квадратов: $\\dfrac{n(n+1)(2n+1)}{6}$',
        ],
      },
    ],
  },
]

export default allFormulas
