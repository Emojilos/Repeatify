-- Migration: Seed problems data (95 problems, 5 per task type)
-- Each task_number (1-19) gets 5 problems with varied difficulty

-- Helper: insert problems referencing topics by task_number
-- Task 1: Планиметрия (базовая)
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 1, 'basic'::problem_difficulty,
  'На клетчатой бумаге с размером клетки $1 \times 1$ изображён треугольник. Найдите его площадь.',
  '6', 0,
  E'## Решение\n\nИспользуем формулу Пика или непосредственное вычисление.\n\nЕсли основание треугольника $a = 4$, а высота $h = 3$, то:\n\n$$S = \\frac{1}{2} \\cdot a \\cdot h = \\frac{1}{2} \\cdot 4 \\cdot 3 = 6$$\n\n**Ответ:** $6$',
  '["Попробуйте использовать формулу площади треугольника через основание и высоту", "Подсчитайте длину основания и высоту по клеткам"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 1;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 1, 'basic'::problem_difficulty,
  'В треугольнике $ABC$ угол $C$ равен $90°$, $AC = 3$, $BC = 4$. Найдите длину гипотенузы $AB$.',
  '5', 0,
  E'## Решение\n\nПо теореме Пифагора:\n\n$$AB^2 = AC^2 + BC^2 = 9 + 16 = 25$$\n\n$$AB = \\sqrt{25} = 5$$\n\n**Ответ:** $5$',
  '["Вспомните теорему Пифагора", "Египетский треугольник: 3, 4, 5"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 1;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 1, 'medium'::problem_difficulty,
  'В параллелограмме $ABCD$ сторона $AB = 8$, высота, проведённая к стороне $AB$, равна $5$. Найдите площадь параллелограмма.',
  '40', 0,
  E'## Решение\n\nПлощадь параллелограмма равна произведению стороны на высоту:\n\n$$S = AB \\cdot h = 8 \\cdot 5 = 40$$\n\n**Ответ:** $40$',
  '["Формула площади параллелограмма: S = a · h"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 1;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 1, 'medium'::problem_difficulty,
  'Диагонали ромба равны $10$ и $24$. Найдите сторону ромба.',
  '13', 0,
  E'## Решение\n\nДиагонали ромба пересекаются под прямым углом и делят друг друга пополам.\n\nПоловины диагоналей: $5$ и $12$.\n\nСторона ромба:\n\n$$a = \\sqrt{5^2 + 12^2} = \\sqrt{25 + 144} = \\sqrt{169} = 13$$\n\n**Ответ:** $13$',
  '["Диагонали ромба перпендикулярны и делятся пополам", "Примените теорему Пифагора"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 1;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 1, 'hard'::problem_difficulty,
  'В прямоугольном треугольнике катет равен $7$, а гипотенуза равна $25$. Найдите площадь треугольника.',
  '84', 0,
  E'## Решение\n\nВторой катет: $b = \\sqrt{25^2 - 7^2} = \\sqrt{576} = 24$.\n\n$$S = \\frac{1}{2} \\cdot 7 \\cdot 24 = 84$$\n\n**Ответ:** $84$',
  '["Сначала найдите второй катет", "Площадь = половина произведения катетов"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 1;

-- Task 2: Вычисления и преобразования
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 2, 'basic'::problem_difficulty,
  E'Найдите значение выражения $\\frac{3^5 \\cdot 3^{-3}}{3^4}$.',
  '0.111111', 0.001,
  E'## Решение\n\n$$\\frac{3^5 \\cdot 3^{-3}}{3^4} = \\frac{3^{2}}{3^4} = 3^{-2} = \\frac{1}{9}$$\n\n**Ответ:** $\\frac{1}{9}$',
  '["Используйте свойство: $a^m \\cdot a^n = a^{m+n}$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 2;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 2, 'basic'::problem_difficulty,
  E'Найдите значение выражения $\\sqrt{75} + \\sqrt{27}$.',
  '8.66', 0.01,
  E'## Решение\n\n$$\\sqrt{75} = 5\\sqrt{3}, \\quad \\sqrt{27} = 3\\sqrt{3}$$\n\n$$5\\sqrt{3} + 3\\sqrt{3} = 8\\sqrt{3} \\approx 8{,}66$$\n\n**Ответ:** $8\\sqrt{3}$',
  '["Вынесите множители из-под корня"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 2;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 2, 'medium'::problem_difficulty,
  E'Найдите значение выражения $\\log_2 48 - \\log_2 3$.',
  '4', 0,
  E'## Решение\n\n$$\\log_2 48 - \\log_2 3 = \\log_2 \\frac{48}{3} = \\log_2 16 = 4$$\n\n**Ответ:** $4$',
  '["$\\log_a b - \\log_a c = \\log_a \\frac{b}{c}$"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 2;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 2, 'medium'::problem_difficulty,
  E'Найдите значение выражения $\\frac{6^7 \\cdot 2^{-7}}{3^5}$.',
  '9', 0,
  E'## Решение\n\n$$\\frac{6^7 \\cdot 2^{-7}}{3^5} = \\frac{(2 \\cdot 3)^7 \\cdot 2^{-7}}{3^5} = \\frac{3^7}{3^5} = 9$$\n\n**Ответ:** $9$',
  '["Представьте $6 = 2 \\cdot 3$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 2;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 2, 'hard'::problem_difficulty,
  E'Найдите значение выражения $\\frac{\\sin 150° \\cdot \\cos 240°}{\\tan 135°}$.',
  '0.25', 0.001,
  E'## Решение\n\n$\\sin 150° = \\frac{1}{2}$, $\\cos 240° = -\\frac{1}{2}$, $\\tan 135° = -1$.\n\n$$\\frac{\\frac{1}{2} \\cdot (-\\frac{1}{2})}{-1} = \\frac{1}{4} = 0{,}25$$\n\n**Ответ:** $0{,}25$',
  '["Используйте формулы приведения"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 2;

-- Task 3: Стереометрия (базовая)
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 3, 'basic'::problem_difficulty,
  'Найдите объём прямоугольного параллелепипеда с рёбрами $3$, $4$ и $5$.',
  '60', 0,
  E'## Решение\n\n$$V = 3 \\cdot 4 \\cdot 5 = 60$$\n\n**Ответ:** $60$',
  '["V = a · b · c"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 3;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 3, 'basic'::problem_difficulty,
  'Площадь поверхности куба равна $54$. Найдите его объём.',
  '27', 0,
  E'## Решение\n\n$S = 6a^2 = 54$, $a^2 = 9$, $a = 3$.\n\n$V = a^3 = 27$.\n\n**Ответ:** $27$',
  '["S = 6a²"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 3;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 3, 'medium'::problem_difficulty,
  E'Цилиндр имеет радиус основания $3$ и высоту $5$. Найдите $\\frac{V}{\\pi}$.',
  '45', 0,
  E'## Решение\n\n$V = \\pi r^2 h = 45\\pi$, $\\frac{V}{\\pi} = 45$.\n\n**Ответ:** $45$',
  '["V = πr²h"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 3;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 3, 'medium'::problem_difficulty,
  'Конус имеет радиус основания $6$ и образующую $10$. Найдите высоту конуса.',
  '8', 0,
  E'## Решение\n\n$$h = \\sqrt{l^2 - r^2} = \\sqrt{100 - 36} = \\sqrt{64} = 8$$\n\n**Ответ:** $8$',
  '["Образующая — гипотенуза прямоугольного треугольника"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 3;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 3, 'hard'::problem_difficulty,
  'Сфера вписана в куб с ребром $6$. Найдите объём сферы. Ответ дайте в виде числа, делённого на $\pi$.',
  '36', 0,
  E'## Решение\n\nРадиус вписанной сферы = половина ребра: $r = 3$.\n\n$$V = \\frac{4}{3}\\pi r^3 = \\frac{4}{3}\\pi \\cdot 27 = 36\\pi$$\n\n$$\\frac{V}{\\pi} = 36$$\n\n**Ответ:** $36$',
  '["Радиус вписанной в куб сферы = a/2"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 3;

-- Task 4: Теория вероятностей
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 4, 'basic'::problem_difficulty,
  'В урне $5$ красных и $3$ синих шара. Наугад вынимают один шар. Какова вероятность того, что он окажется красным?',
  '0.625', 0.001,
  E'## Решение\n\n$$P = \\frac{5}{8} = 0{,}625$$\n\n**Ответ:** $0{,}625$',
  '["P = благоприятные / все исходы"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 4;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 4, 'basic'::problem_difficulty,
  'Вероятность брака батарейки равна $0{,}02$. Найдите вероятность того, что купленная батарейка исправна.',
  '0.98', 0.001,
  E'## Решение\n\n$$P = 1 - 0{,}02 = 0{,}98$$\n\n**Ответ:** $0{,}98$',
  '["P(A) + P(не A) = 1"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 4;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 4, 'medium'::problem_difficulty,
  'Два стрелка стреляют. Вероятности попадания: $0{,}7$ и $0{,}8$. Найдите вероятность хотя бы одного попадания.',
  '0.94', 0.001,
  E'## Решение\n\n$$P = 1 - (1-0{,}7)(1-0{,}8) = 1 - 0{,}06 = 0{,}94$$\n\n**Ответ:** $0{,}94$',
  '["P(хотя бы одно) = 1 − P(ни одного)"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 4;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 4, 'medium'::problem_difficulty,
  'В группе $20$ студентов, $8$ девушек. Выбирают двоих. Вероятность, что обе — девушки?',
  '0.147', 0.001,
  E'## Решение\n\n$$P = \\frac{C_8^2}{C_{20}^2} = \\frac{28}{190} \\approx 0{,}147$$\n\n**Ответ:** $0{,}147$',
  '["$C_n^k = \\frac{n!}{k!(n-k)!}$"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 4;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 4, 'hard'::problem_difficulty,
  'Монету подбрасывают $4$ раза. Вероятность ровно $2$ орлов?',
  '0.375', 0.001,
  E'## Решение\n\n$$P = C_4^2 \\cdot (\\frac{1}{2})^4 = \\frac{6}{16} = 0{,}375$$\n\n**Ответ:** $0{,}375$',
  '["Формула Бернулли"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 4;

-- Task 5: Уравнения
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 5, 'basic'::problem_difficulty,
  'Решите уравнение $2x - 7 = 3$.',
  '5', 0,
  E'## Решение\n\n$2x = 10$, $x = 5$.\n\n**Ответ:** $5$',
  '["Перенесите −7 в правую часть"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 5;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 5, 'basic'::problem_difficulty,
  'Решите $x^2 - 5x + 6 = 0$. Укажите наибольший корень.',
  '3', 0,
  E'## Решение\n\n$(x-2)(x-3) = 0$, $x = 2$ или $x = 3$. Наибольший: $3$.\n\n**Ответ:** $3$',
  '["Разложите на множители"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 5;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 5, 'medium'::problem_difficulty,
  E'Решите уравнение $\\log_3(2x - 1) = 2$.',
  '5', 0,
  E'## Решение\n\n$2x - 1 = 9$, $x = 5$. ОДЗ: $2·5-1 = 9 > 0$ ✓\n\n**Ответ:** $5$',
  '["$\\log_a b = c \\Leftrightarrow b = a^c$"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 5;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 5, 'medium'::problem_difficulty,
  'Решите уравнение $3^{2x-1} = 27$.',
  '2', 0,
  E'## Решение\n\n$3^{2x-1} = 3^3$, $2x-1 = 3$, $x = 2$.\n\n**Ответ:** $2$',
  '["27 = 3³"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 5;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 5, 'hard'::problem_difficulty,
  E'Решите $2\\cos^2 x - 3\\cos x + 1 = 0$. Наименьший положительный корень (в градусах).',
  '60', 0,
  E'## Решение\n\nЗамена $t = \\cos x$: $(2t-1)(t-1) = 0$.\n\n$\\cos x = 1/2$: $x = 60°$. $\\cos x = 1$: $x = 0°$ (не положительный).\n\n**Ответ:** $60$',
  '["Замена t = cos x"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 5;

-- Task 6: Планиметрия (вычислительная)
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 6, 'basic'::problem_difficulty,
  E'В треугольнике $ABC$ угол $A = 30°$, $BC = 5$. Найдите радиус описанной окружности.',
  '5', 0,
  E'## Решение\n\n$\\frac{BC}{\\sin A} = 2R$, $R = \\frac{5}{2 \\cdot 0{,}5} = 5$.\n\n**Ответ:** $5$',
  '["Теорема синусов"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 6;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 6, 'basic'::problem_difficulty,
  'В окружность вписан четырёхугольник $ABCD$. Угол $A = 110°$. Найдите угол $C$.',
  '70', 0,
  E'## Решение\n\nСумма противоположных углов = $180°$: $C = 180° - 110° = 70°$.\n\n**Ответ:** $70$',
  '["Сумма противоположных углов вписанного четырёхугольника = 180°"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 6;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 6, 'medium'::problem_difficulty,
  'В треугольнике стороны $13$, $14$, $15$. Найдите площадь.',
  '84', 0.01,
  E'## Решение\n\nФормула Герона: $p = 21$.\n\n$S = \\sqrt{21 \\cdot 8 \\cdot 7 \\cdot 6} = \\sqrt{7056} = 84$.\n\n**Ответ:** $84$',
  '["Формула Герона"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 6;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 6, 'medium'::problem_difficulty,
  E'Хорда стягивает дугу $120°$ в окружности радиуса $10$. Длина хорды?',
  '17.32', 0.01,
  E'## Решение\n\n$AB = 2R\\sin(\\alpha/2) = 20\\sin 60° = 10\\sqrt{3} \\approx 17{,}32$.\n\n**Ответ:** $10\\sqrt{3}$',
  '["Длина хорды: $2R\\sin(\\alpha/2)$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 6;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 6, 'hard'::problem_difficulty,
  'Биссектриса угла $A$ в $\\triangle ABC$ ($AB=6$, $AC=10$, $BC=8$) пересекает $BC$ в точке $D$. Найдите $BD$.',
  '3', 0,
  E'## Решение\n\n$\\frac{BD}{DC} = \\frac{AB}{AC} = \\frac{6}{10} = \\frac{3}{5}$.\n\n$BD = 3k$, $DC = 5k$, $8k = 8$, $k = 1$, $BD = 3$.\n\n**Ответ:** $3$',
  '["Биссектриса делит противоположную сторону в отношении прилежащих сторон"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 6;

-- Task 7: Производная и первообразная
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 7, 'basic'::problem_difficulty,
  E'Найдите $f''(1)$ для $f(x) = x^3 - 2x^2 + 5x$.',
  '4', 0,
  E'## Решение\n\n$f''(x) = 3x^2 - 4x + 5$, $f''(1) = 3 - 4 + 5 = 4$.\n\n**Ответ:** $4$',
  '["$(x^n)'' = nx^{n-1}$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 7;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 7, 'basic'::problem_difficulty,
  'Касательная к графику $f(x)$ проходит через $(1, 2)$ и $(5, 6)$. Чему равна производная в точке касания?',
  '1', 0,
  E'## Решение\n\n$f''(x_0) = k = \\frac{6-2}{5-1} = 1$.\n\n**Ответ:** $1$',
  '["Производная = угловой коэффициент касательной"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 7;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 7, 'medium'::problem_difficulty,
  'Найдите точку максимума $f(x) = x^3 - 12x + 5$.',
  '-2', 0,
  E'## Решение\n\n$f''(x) = 3x^2 - 12 = 0$, $x = \\pm 2$.\n\nМаксимум при $x = -2$ (смена + на −).\n\n**Ответ:** $-2$',
  '["$f''(x) = 0$, определите знак"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 7;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 7, 'medium'::problem_difficulty,
  'Точка движется по закону $x(t) = t^3 - 3t^2 + 2$. Скорость при $t = 2$?',
  '0', 0,
  E'## Решение\n\n$v(t) = 3t^2 - 6t$, $v(2) = 12 - 12 = 0$.\n\n**Ответ:** $0$',
  '["Скорость = производная координаты"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 7;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 7, 'hard'::problem_difficulty,
  E'Найдите значение первообразной $F(x) = x^4 + 3x^2 - x + C$ функции $f(x) = 4x^3 + 6x - 1$ в точке $x = 0$, если $F(1) = 5$.',
  '2', 0,
  E'## Решение\n\n$F(1) = 1 + 3 - 1 + C = 5$, $C = 2$.\n\n$F(0) = 0 + 0 - 0 + 2 = 2$.\n\n**Ответ:** $2$',
  '["Проинтегрируйте и найдите C"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 7;

-- Task 8: Прикладные задачи
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 8, 'basic'::problem_difficulty,
  'Тетрадь стоит $40$ руб. Цена выросла на $10\%$. Сколько тетрадей можно купить на $750$ руб.?',
  '17', 0,
  E'## Решение\n\nНовая цена: $44$ руб. $\\lfloor 750/44 \\rfloor = 17$.\n\n**Ответ:** $17$',
  '["Новая цена = 40 · 1.1"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 8;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 8, 'basic'::problem_difficulty,
  'Сколько месяцев средняя температура была выше $10°C$, если по месяцам: $-8, -6, 2, 8, 14, 18, 22, 20, 14, 8, 2, -4$?',
  '5', 0,
  E'## Решение\n\nМай 14, Июнь 18, Июль 22, Август 20, Сентябрь 14 — всего $5$.\n\n**Ответ:** $5$',
  '["Подсчитайте месяцы с T > 10"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 8;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 8, 'medium'::problem_difficulty,
  'Первую половину пути — $60$ км/ч, вторую — $40$ км/ч. Средняя скорость?',
  '48', 0,
  E'## Решение\n\n$v = \\frac{2 \\cdot 60 \\cdot 40}{60 + 40} = \\frac{4800}{100} = 48$.\n\n**Ответ:** $48$',
  '["$v = \\frac{2v_1 v_2}{v_1 + v_2}$"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 8;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 8, 'medium'::problem_difficulty,
  '$10000$ руб. под $5\%$ годовых (сложный процент). Сумма через $2$ года?',
  '11025', 1,
  E'## Решение\n\n$S = 10000 \\cdot 1{,}05^2 = 11025$.\n\n**Ответ:** $11025$',
  '["$S = S_0(1+r)^n$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 8;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 8, 'hard'::problem_difficulty,
  'Прямоугольный участок площадью $6$ га, ширина на $100$ м меньше длины. Длина (в м)?',
  '300', 0,
  E'## Решение\n\n$x(x-100) = 60000$. $x^2 - 100x - 60000 = 0$. $x = 300$.\n\n**Ответ:** $300$',
  '["1 га = 10000 м²"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 8;

-- Task 9: Функции и графики
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 9, 'basic'::problem_difficulty,
  'Наименьшее значение $f(x) = x^2 - 6x + 13$?',
  '4', 0,
  E'## Решение\n\n$f(x) = (x-3)^2 + 4$. Минимум: $4$ при $x = 3$.\n\n**Ответ:** $4$',
  '["Выделите полный квадрат"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 9;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 9, 'basic'::problem_difficulty,
  'Парабола $f(x) = (x-2)^2 - 1$. Найдите $f(0)$.',
  '3', 0,
  E'## Решение\n\n$f(0) = (0-2)^2 - 1 = 4 - 1 = 3$.\n\n**Ответ:** $3$',
  '["Подставьте x = 0"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 9;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 9, 'medium'::problem_difficulty,
  'Сколько точек пересечения у $y = |x - 2|$ и $y = 3$?',
  '2', 0,
  E'## Решение\n\n$|x-2| = 3$: $x = 5$ или $x = -1$. Две точки.\n\n**Ответ:** $2$',
  '["Раскройте модуль"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 9;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 9, 'medium'::problem_difficulty,
  E'Длина области определения $f(x) = \\sqrt{4 - x^2}$?',
  '4', 0,
  E'## Решение\n\n$4 - x^2 \\geq 0$, $-2 \\leq x \\leq 2$. Длина: $4$.\n\n**Ответ:** $4$',
  '["Подкоренное ≥ 0"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 9;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 9, 'hard'::problem_difficulty,
  E'Наименьшее значение $f(x) = x + \\frac{1}{x}$ на $(0, +\\infty)$?',
  '2', 0,
  E'## Решение\n\nПо неравенству AM-GM: $x + 1/x \\geq 2$, равенство при $x = 1$.\n\n**Ответ:** $2$',
  '["Неравенство AM-GM"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 9;

-- Task 10: Текстовые задачи
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 10, 'basic'::problem_difficulty,
  'Из $A$ в $B$ ($360$ км) выехал автомобиль ($80$ км/ч). Через $1$ ч навстречу — другой ($60$ км/ч). Через сколько часов после выезда второго они встретятся?',
  '2', 0,
  E'## Решение\n\nОсталось $280$ км. Скорость сближения $140$ км/ч. Время: $2$ ч.\n\n**Ответ:** $2$',
  '["Скорость сближения = v₁ + v₂"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 10;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 10, 'basic'::problem_difficulty,
  '$4$ рабочих — $15$ дней. За сколько дней $6$ рабочих?',
  '10', 0,
  E'## Решение\n\nОбъём: $60$ чел.-дн. $60/6 = 10$ дн.\n\n**Ответ:** $10$',
  '["Объём работы = кол-во × время"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 10;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 10, 'medium'::problem_difficulty,
  'Трубы заполняют бассейн за $20$ и $30$ мин. Вместе — за сколько минут?',
  '12', 0,
  E'## Решение\n\n$1/20 + 1/30 = 5/60 = 1/12$. Время: $12$ мин.\n\n**Ответ:** $12$',
  '["Сложите производительности"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 10;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 10, 'medium'::problem_difficulty,
  '$3$ л $20\\%$-ного + $7$ л $40\\%$-ного раствора. Концентрация смеси (%)?',
  '34', 0,
  E'## Решение\n\nСоль: $0{,}6 + 2{,}8 = 3{,}4$ л. Концентрация: $3{,}4/10 = 34\\%$.\n\n**Ответ:** $34$',
  '["Масса вещества = объём × концентрация"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 10;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 10, 'hard'::problem_difficulty,
  'Лодка: $24$ км по течению + $24$ км против, всего $9$ ч. Течение $2$ км/ч. Собственная скорость?',
  '6', 0,
  E'## Решение\n\n$24/(v+2) + 24/(v-2) = 9$. При $v=6$: $24/8 + 24/4 = 3 + 6 = 9$ ✓.\n\n**Ответ:** $6$',
  '["Составьте уравнение с v"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 10;

-- Task 11: Последовательности
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 11, 'basic'::problem_difficulty,
  'АП: $a_1 = 3$, $d = 4$. Найдите $a_{10}$.',
  '39', 0,
  E'## Решение\n\n$a_{10} = 3 + 9 \\cdot 4 = 39$.\n\n**Ответ:** $39$',
  '["$a_n = a_1 + (n-1)d$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 11;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 11, 'basic'::problem_difficulty,
  'ГП: $b_1 = 2$, $q = 3$. Найдите $b_5$.',
  '162', 0,
  E'## Решение\n\n$b_5 = 2 \\cdot 3^4 = 162$.\n\n**Ответ:** $162$',
  '["$b_n = b_1 q^{n-1}$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 11;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 11, 'medium'::problem_difficulty,
  'Сумма первых $20$ членов АП: $a_1 = 5$, $a_{20} = 62$.',
  '670', 0,
  E'## Решение\n\n$S = 20(5+62)/2 = 670$.\n\n**Ответ:** $670$',
  '["$S_n = n(a_1 + a_n)/2$"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 11;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 11, 'medium'::problem_difficulty,
  'Бесконечная убывающая ГП: $S = 8$, $b_1 = 4$. Знаменатель?',
  '0.5', 0.001,
  E'## Решение\n\n$8 = 4/(1-q)$, $1-q = 0{,}5$, $q = 0{,}5$.\n\n**Ответ:** $0{,}5$',
  '["$S = b_1/(1-q)$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 11;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 11, 'hard'::problem_difficulty,
  'АП: $S_5 = 35$, $S_{10} = 120$. Найдите $a_1$.',
  '3', 0,
  E'## Решение\n\n$5a_1 + 10d = 35$, $10a_1 + 45d = 120$.\n\n$d = 2$, $a_1 = 3$.\n\n**Ответ:** $3$',
  '["Составьте систему уравнений"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 11;

-- Task 12: Наибольшее и наименьшее значение
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 12, 'basic'::problem_difficulty,
  'Наименьшее значение $x^2 + 4x + 8$ на $[-5, 0]$.',
  '4', 0,
  E'## Решение\n\n$f''(x) = 2x+4 = 0$, $x = -2$.\n$f(-5) = 13$, $f(-2) = 4$, $f(0) = 8$. Минимум: $4$.\n\n**Ответ:** $4$',
  '["Проверьте критические точки и концы"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 12;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 12, 'basic'::problem_difficulty,
  'Наибольшее значение $-x^2 + 6x - 5$ на $[0, 5]$.',
  '4', 0,
  E'## Решение\n\n$f''(x) = -2x+6 = 0$, $x = 3$.\n$f(0) = -5$, $f(3) = 4$, $f(5) = 0$. Максимум: $4$.\n\n**Ответ:** $4$',
  '["Вершина параболы"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 12;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 12, 'medium'::problem_difficulty,
  'Наименьшее значение $2x^3 - 9x^2 + 12x + 1$ на $[1, 3]$.',
  '5', 0,
  E'## Решение\n\n$f''(x) = 6(x-1)(x-2) = 0$. На $[1,3]$: $f(1)=6$, $f(2)=5$, $f(3)=10$. Мин: $5$.\n\n**Ответ:** $5$',
  '["Найдите критические точки на отрезке"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 12;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 12, 'medium'::problem_difficulty,
  E'Наибольшее значение $\\ln(x+1) - x$ на $[0, 2]$.',
  '0', 0.001,
  E'## Решение\n\n$f''(x) = 1/(x+1) - 1 = -x/(x+1) \\leq 0$ на $(0,2]$. Убывает. Максимум в $x=0$: $f(0) = 0$.\n\n**Ответ:** $0$',
  '["Определите монотонность"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 12;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 12, 'hard'::problem_difficulty,
  E'Наименьшее значение $e^{2x} - 6e^x + 5$.',
  '-4', 0,
  E'## Решение\n\nЗамена $t = e^x > 0$: $g(t) = t^2 - 6t + 5 = (t-3)^2 - 4$. Минимум: $-4$ при $t = 3$.\n\n**Ответ:** $-4$',
  '["Замена $t = e^x$"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 12;

-- Task 13: Стереометрия (профильная) — Part 2, no correct_answer
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 13, 'medium'::problem_difficulty,
  E'В правильной треугольной призме $ABCA_1B_1C_1$ все рёбра равны $2$. Найдите расстояние от $A$ до плоскости $A_1B_1C$.',
  NULL, 0,
  E'## Решение\n\nКоординаты: $A(0,0,0)$, $B(2,0,0)$, $C(1,\\sqrt{3},0)$, $A_1(0,0,2)$, $B_1(2,0,2)$.\n\nНормаль к плоскости $A_1B_1C$: $\\vec{n} = (0, 2, \\sqrt{3})$.\n\nРасстояние: $d = \\frac{2\\sqrt{3}}{\\sqrt{7}} = \\frac{2\\sqrt{21}}{7}$.\n\n**Ответ:** $\\frac{2\\sqrt{21}}{7}$',
  '["Координатный метод", "Формула расстояния от точки до плоскости"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 13;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 13, 'medium'::problem_difficulty,
  'В правильной четырёхугольной пирамиде $SABCD$: $AB = 4$, $SO = 6$. Угол между гранью $SAB$ и основанием?',
  NULL, 0,
  E'## Решение\n\n$OM = 2$, $SO = 6$. $\\tan\\alpha = 6/2 = 3$. $\\alpha = \\arctan 3$.\n\n**Ответ:** $\\arctan 3$',
  '["Найдите двугранный угол через линейный угол"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 13;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 13, 'hard'::problem_difficulty,
  E'В кубе с ребром $1$ расстояние между прямыми $AB_1$ и $BD_1$?',
  NULL, 0,
  E'## Решение\n\n$\\vec{u} = (1,0,1)$, $\\vec{v} = (-1,1,1)$, $\\vec{n} = (-1,-2,1)$.\n\n$d = \\frac{|(1,0,0) \\cdot (-1,-2,1)|}{\\sqrt{6}} = \\frac{1}{\\sqrt{6}} = \\frac{\\sqrt{6}}{6}$.\n\n**Ответ:** $\\frac{\\sqrt{6}}{6}$',
  '["Формула расстояния между скрещивающимися прямыми"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 13;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 13, 'medium'::problem_difficulty,
  'Параллелепипед $ABCDA_1B_1C_1D_1$: $AB=3$, $BC=4$, $AA_1=5$. Диагональ $AC_1$?',
  NULL, 0,
  E'## Решение\n\n$AC_1 = \\sqrt{9+16+25} = \\sqrt{50} = 5\\sqrt{2}$.\n\n**Ответ:** $5\\sqrt{2}$',
  '["$d = \\sqrt{a^2+b^2+c^2}$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 13;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 13, 'hard'::problem_difficulty,
  'В правильном тетраэдре с ребром $a$ найдите угол между плоскостями $ABC$ и $ABD$.',
  NULL, 0,
  E'## Решение\n\nДвугранный угол при ребре $AB$: $\\cos\\alpha = 1/3$.\n\n$\\alpha = \\arccos(1/3) \\approx 70{,}53°$.\n\n**Ответ:** $\\arccos\\frac{1}{3}$',
  '["Найдите двугранный угол при ребре AB"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 13;

-- Task 14: Неравенства — Part 2
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 14, 'medium'::problem_difficulty,
  E'Решите $\\log_2(x-1) + \\log_2(x+1) \\leq 3$.',
  NULL, 0,
  E'## Решение\n\nОДЗ: $x > 1$. $\\log_2(x^2-1) \\leq 3$, $x^2 \\leq 9$.\n\nОтвет: $x \\in (1, 3]$.',
  '["ОДЗ + свойства логарифмов"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 14;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 14, 'medium'::problem_difficulty,
  E'Решите $\\frac{x^2-4}{x+3} \\geq 0$.',
  NULL, 0,
  E'## Решение\n\nМетод интервалов: нули $-2, 2$, полюс $-3$.\n\nОтвет: $(-3, -2] \\cup [2, +\\infty)$.',
  '["Метод интервалов"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 14;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 14, 'hard'::problem_difficulty,
  E'Решите $\\log_{0{,}5}(x^2-3x) > \\log_{0{,}5}(4x-12)$.',
  NULL, 0,
  E'## Решение\n\nОДЗ: $x > 3$. Основание < 1: $x^2-3x < 4x-12$, $(x-3)(x-4) < 0$.\n\nОтвет: $(3, 4)$.',
  '["Основание < 1 — знак меняется"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 14;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 14, 'medium'::problem_difficulty,
  E'Решите $(x-3)(x+2)(x-7) \\leq 0$.',
  NULL, 0,
  E'## Решение\n\nМетод интервалов: $(-\\infty, -2] \\cup [3, 7]$.\n\n**Ответ:** $(-\\infty, -2] \\cup [3, 7]$',
  '["Метод интервалов"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 14;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 14, 'hard'::problem_difficulty,
  E'Решите $3^{x+1} - 4 \\cdot 3^x + 3^{x-1} \\leq 2$.',
  NULL, 0,
  E'## Решение\n\n$3^x(3 - 4 + 1/3) = 3^x \\cdot (-2/3) \\leq 2$. Всегда верно ($3^x > 0$).\n\nОтвет: $x \\in \\mathbb{R}$.',
  '["Вынесите $3^{x-1}$"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 14;

-- Task 15: Финансовая математика — Part 2
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 15, 'medium'::problem_difficulty,
  'Кредит $1\\,000\\,000$ руб. на $2$ года под $10\\%$ (сложные), равные ежегодные платежи. Размер платежа?',
  NULL, 0,
  E'## Решение\n\n$1000000 \\cdot 1{,}21 = 2{,}1x$, $x = 576190$ руб.\n\n**Ответ:** $576\\,190$ руб.',
  '["Каждый год: долг × 1.1 − платёж"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 15;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 15, 'medium'::problem_difficulty,
  '$500\\,000$ руб., $12\\%$ годовых. Через сколько лет > $800\\,000$?',
  NULL, 0,
  E'## Решение\n\n$1{,}12^n > 1{,}6$. $n = 5$: $1{,}12^5 \\approx 1{,}76 > 1{,}6$ ✓.\n\n**Ответ:** $5$ лет.',
  '["Перебор степеней"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 15;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 15, 'hard'::problem_difficulty,
  'Кредит $2\\,000\\,000$ на $3$ года под $20\\%$, дифференцированные платежи. Общая сумма выплат?',
  NULL, 0,
  E'## Решение\n\nОсновной долг: $666\\,667$/год. Проценты: $400\\,000 + 266\\,667 + 133\\,333 = 800\\,000$.\n\nИтого: $2\\,800\\,000$ руб.\n\n**Ответ:** $2\\,800\\,000$',
  '["Проценты на остаток"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 15;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 15, 'medium'::problem_difficulty,
  'Акции: +$20\\%$ в понедельник, −$20\\%$ во вторник. Итоговое изменение?',
  NULL, 0,
  E'## Решение\n\n$100 \\cdot 1{,}2 \\cdot 0{,}8 = 96$. Снизилась на $4\\%$.\n\n**Ответ:** снизилась на $4\\%$',
  '["Возьмите 100 за начальную цену"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 15;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 15, 'hard'::problem_difficulty,
  'Вклад $100\\,000$ руб. Каждый год добавляют $20\\,000$ руб. Ставка $8\\%$. Сумма через $3$ года?',
  NULL, 0,
  E'## Решение\n\n$S_1 = 100000 \\cdot 1{,}08 + 20000 = 128000$\n$S_2 = 128000 \\cdot 1{,}08 + 20000 = 158240$\n$S_3 = 158240 \\cdot 1{,}08 + 20000 = 190899$ (округлённо)\n\n**Ответ:** $\\approx 190\\,899$ руб.',
  '["Каждый год: сумма × 1.08 + 20000"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 15;

-- Task 16: Планиметрия (профильная) — Part 2
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 16, 'medium'::problem_difficulty,
  E'$\\triangle ABC$: $AB=5$, $BC=6$, $\\angle B = 60°$. Найдите $AC$.',
  NULL, 0,
  E'## Решение\n\nТеорема косинусов: $AC^2 = 25 + 36 - 30 = 31$. $AC = \\sqrt{31}$.\n\n**Ответ:** $\\sqrt{31}$',
  '["Теорема косинусов"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 16;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 16, 'hard'::problem_difficulty,
  E'Высоты $AA_1$ и $BB_1$ в остроугольном $\\triangle ABC$. Докажите подобие $\\triangle AA_1C \\sim \\triangle BB_1C$. $AB = 10$, $\\angle C = 30°$. Найдите $A_1B_1$.',
  NULL, 0,
  E'## Решение\n\nОба прямоугольных с общим $\\angle C$ → подобны.\n\n$A_1B_1 = AB\\cos C = 10 \\cdot \\cos 30° = 5\\sqrt{3}$.\n\n**Ответ:** $5\\sqrt{3}$',
  '["Подобие по двум углам", "$A_1B_1 = AB\\cos C$"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 16;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 16, 'hard'::problem_difficulty,
  E'Окружность ($R=5$) вписана в угол $60°$ с вершиной $A$. Расстояние $AO$?',
  NULL, 0,
  E'## Решение\n\n$\\sin 30° = R/AO = 5/AO$, $AO = 10$.\n\n**Ответ:** $10$',
  '["$\\sin(A/2) = R/AO$"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 16;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 16, 'medium'::problem_difficulty,
  'Трапеция $ABCD$ ($AD \\| BC$): $BC=3$, $AD=9$, $S_{BOC}=6$. Площадь трапеции?',
  NULL, 0,
  E'## Решение\n\nКоэфф. подобия $1/3$. $S_{DOA} = 54$. $S_{AOB} = S_{DOC} = 18$.\n\nИтого: $6 + 54 + 18 + 18 = 96$.\n\n**Ответ:** $96$',
  '["Подобие треугольников при пересечении диагоналей"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 16;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 16, 'hard'::problem_difficulty,
  E'Медианы $AM$ и $BN$ в $\\triangle ABC$ пересекаются в $G$. $S_{AGB} = 12$. Найдите $S_{ABC}$.',
  NULL, 0,
  E'## Решение\n\nМедианы делят на 6 равновеликих частей. $S_{AGB} = 2/6 \\cdot S_{ABC}$.\n\n$12 = S_{ABC}/3$, $S_{ABC} = 36$.\n\n**Ответ:** $36$',
  '["Медианы делят треугольник на 6 равновеликих частей"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 16;

-- Task 17: Параметры — Part 2
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 17, 'medium'::problem_difficulty,
  E'При каких $a$ уравнение $x^2 + ax + 1 = 0$ имеет два различных корня?',
  NULL, 0,
  E'## Решение\n\n$D = a^2 - 4 > 0$, $|a| > 2$.\n\nОтвет: $a \\in (-\\infty,-2) \\cup (2,+\\infty)$.',
  '["D > 0"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 17;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 17, 'hard'::problem_difficulty,
  E'При каких $a$ система $x^2+y^2=4$, $y=x+a$ имеет ровно одно решение?',
  NULL, 0,
  E'## Решение\n\nПодставляем: $2x^2+2ax+a^2-4=0$. $D = -4a^2+32 = 0$, $a = \\pm 2\\sqrt{2}$.\n\n**Ответ:** $a = \\pm 2\\sqrt{2}$',
  '["Касательная ↔ D = 0"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 17;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 17, 'hard'::problem_difficulty,
  'При каких $a$ уравнение $|x-1|+|x-3|=a$ имеет бесконечно много решений?',
  NULL, 0,
  E'## Решение\n\nПри $1 \\leq x \\leq 3$: $f(x) = 2$. Бесконечно много решений при $a = 2$.\n\n**Ответ:** $a = 2$',
  '["Раскройте модули на интервалах"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 17;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 17, 'medium'::problem_difficulty,
  'При каких $a$ уравнение $ax^2 - 2x + 1 = 0$ имеет хотя бы один корень?',
  NULL, 0,
  E'## Решение\n\nПри $a = 0$: $x = 1/2$. При $a \\neq 0$: $D = 4 - 4a \\geq 0$, $a \\leq 1$.\n\nОтвет: $a \\leq 1$.',
  '["Случай a = 0 отдельно"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 17;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 17, 'hard'::problem_difficulty,
  E'При каких $a$ неравенство $(x-a)^2 \\leq 1$ содержит ровно 3 целых числа?',
  NULL, 0,
  E'## Решение\n\n$|x-a| \\leq 1$, отрезок $[a-1, a+1]$ длины 2. Содержит 3 целых при целом $a$.\n\n**Ответ:** $a \\in \\mathbb{Z}$',
  '["Выделите полный квадрат"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 17;

-- Task 18: Числа и их свойства — Part 2
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 18, 'medium'::problem_difficulty,
  E'Найдите все пары натуральных $(x,y)$: $\\frac{1}{x}+\\frac{1}{y}=\\frac{1}{6}$.',
  NULL, 0,
  E'## Решение\n\n$(x-6)(y-6) = 36$. Пары: $(7,42),(8,24),(9,18),(10,15),(12,12)$ и симм.\n\n**Ответ:** $(7,42),(8,24),(9,18),(10,15),(12,12)$',
  '["Факторизация через прибавление 36"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 18;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 18, 'medium'::problem_difficulty,
  E'Докажите: $n^3 - n$ делится на $6$ для любого натурального $n$.',
  NULL, 0,
  E'## Решение\n\n$n^3 - n = (n-1)n(n+1)$ — произведение 3 последовательных чисел, делится на $2$ и $3$, значит на $6$.\n\n**Ответ:** доказано.',
  '["Разложите на множители"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 18;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 18, 'hard'::problem_difficulty,
  'Существует ли $n$: остаток от деления на $7$ равен $5$, на $11$ — равен $3$?',
  NULL, 0,
  E'## Решение\n\n$n = 7k+5 = 11m+3$. При $m=4$: $k=6$, $n=47$. Проверка: $47=6·7+5$ ✓, $47=4·11+3$ ✓.\n\n**Ответ:** да, $n = 47$.',
  '["Китайская теорема об остатках"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 18;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 18, 'hard'::problem_difficulty,
  E'НОД($2^{30}-1$, $2^{18}-1$)?',
  NULL, 0,
  E'## Решение\n\nНОД$(2^a-1, 2^b-1) = 2^{\\text{НОД}(a,b)}-1$.\n\nНОД$(30,18) = 6$, ответ: $2^6-1 = 63$.\n\n**Ответ:** $63$',
  '["НОД(2^a−1, 2^b−1) = 2^{НОД(a,b)}−1"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 18;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 18, 'medium'::problem_difficulty,
  E'При каких натуральных $n$ выражение $n^2+3n+7$ делится на $n+1$?',
  NULL, 0,
  E'## Решение\n\n$n^2+3n+7 = (n+1)(n+2)+5$. Делится на $n+1$ когда $5 \\vdots (n+1)$.\n\n$n+1 \\in \\{1,5\\}$, $n = 4$.\n\n**Ответ:** $n = 4$',
  '["Деление с остатком"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 18;

-- Task 19: Комбинаторика и логика — Part 2
INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 19, 'medium'::problem_difficulty,
  'Числа $1$–$20$. Стираем два, пишем $|a-b|$. Наименьшее оставшееся после $19$ ходов?',
  NULL, 0,
  E'## Решение\n\nСумма $210$ — чётная. Инвариант: чётность суммы. Можно разбить на 2 группы с суммой $105$ → результат $0$.\n\n**Ответ:** $0$',
  '["Инвариант чётности"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 19;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 19, 'medium'::problem_difficulty,
  '$10$ стульев в ряд, $4$ человека, никакие два не рядом. Сколько способов?',
  NULL, 0,
  E'## Решение\n\nВыбор стульев: $C_7^4 = 35$. Рассадка: $4! = 24$. Итого: $840$.\n\n**Ответ:** $840$',
  '["Замена для непоследовательных мест"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 19;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 19, 'hard'::problem_difficulty,
  E'Последовательность: $a_1=1$, $a_{i+1} = 2a_i$ или $a_i - 1$. Может ли $a_{2025} = 2025$?',
  NULL, 0,
  E'## Решение\n\nПуть: 11 удвоений до 2048, 23 вычитания до 2025 = 34 шага. Осталось 1990 шагов: цикл $1→2→1$ × 995 = 1990 шагов.\n\n**Ответ:** да',
  '["Найдите путь + используйте циклы"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 19;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 19, 'hard'::problem_difficulty,
  '$100$ монет в ряд ($50$ орлов, $50$ решек). Переворот $3$ подряд. Можно ли сделать все орлом?',
  NULL, 0,
  E'## Решение\n\nИнвариант: чётность суммы (50 — чётная, 0 — чётная). Каждая операция меняет чётность, значит нужно чётное число операций. Комбинации операций позволяют перевернуть любую пару. Можно.\n\n**Ответ:** да, всегда можно',
  '["Инвариант чётности", "Комбинация операций"]'::jsonb,
  'Ященко И.В., Типовые варианты ЕГЭ'
FROM topics t WHERE t.task_number = 19;

INSERT INTO problems (topic_id, task_number, difficulty, problem_text, correct_answer, answer_tolerance, solution_markdown, hints, source)
SELECT t.id, 19, 'medium'::problem_difficulty,
  'Из цифр $1,2,3,4,5$ (каждая по разу) — пятизначные числа, делящиеся на $4$. Сколько?',
  NULL, 0,
  E'## Решение\n\nПоследние 2 цифры кратны 4: $12, 24, 32, 52$ — 4 варианта. Остальные 3 цифры: $3! = 6$.\n\nИтого: $24$.\n\n**Ответ:** $24$',
  '["Делимость на 4 ↔ последние 2 цифры"]'::jsonb,
  'ФИПИ, Открытый банк заданий ЕГЭ'
FROM topics t WHERE t.task_number = 19;
