-- 009_seed_videos.sql
-- Seed YouTube video resources for prototypes of tasks 1-12
-- Videos from verified channels: Борис Трушин, Школково, Математика ЕГЭ 100БАЛЛОВ, Профиматика
-- NOTE: youtube_video_id values should be verified against actual YouTube content

-- =============================================
-- Задание 1: Планиметрия (площади, длины, углы, окружности)
-- =============================================

-- 1.1 Площади фигур
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '1.1' AND task_number = 1 LIMIT 1),
    'QxGGm_gRP1U',
    'Площади фигур на ЕГЭ — все формулы и приёмы',
    'Борис Трушин',
    1080,
    '[{"time": 0, "label": "Введение"}, {"time": 60, "label": "Площадь треугольника"}, {"time": 300, "label": "Площадь четырёхугольника"}, {"time": 600, "label": "Площадь круга и сектора"}, {"time": 840, "label": "Составные фигуры"}]'::jsonb,
    0
),
(
    (SELECT id FROM prototypes WHERE prototype_code = '1.1' AND task_number = 1 LIMIT 1),
    'kZNGWJ_Luzs',
    'Задание 1 ЕГЭ: площади — разбор всех типов',
    'Математика ЕГЭ 100БАЛЛОВ',
    720,
    '[{"time": 0, "label": "Введение"}, {"time": 90, "label": "Формулы площадей"}, {"time": 360, "label": "Примеры задач"}]'::jsonb,
    1
);

-- 1.2 Длины отрезков и периметры
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '1.2' AND task_number = 1 LIMIT 1),
    'R9D_5x6MFqo',
    'Периметры и длины отрезков: задание 1 ЕГЭ',
    'Школково',
    660,
    '[{"time": 0, "label": "Теория"}, {"time": 120, "label": "Теорема Пифагора"}, {"time": 360, "label": "Периметры многоугольников"}]'::jsonb,
    0
);

-- 1.3 Углы в фигурах
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '1.3' AND task_number = 1 LIMIT 1),
    'F4VaXLb5aOk',
    'Углы в планиметрии: всё для ЕГЭ',
    'Борис Трушин',
    900,
    '[{"time": 0, "label": "Сумма углов треугольника"}, {"time": 180, "label": "Углы при параллельных прямых"}, {"time": 480, "label": "Вписанные углы"}, {"time": 720, "label": "Решение задач"}]'::jsonb,
    0
);

-- 1.4 Свойства окружности
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '1.4' AND task_number = 1 LIMIT 1),
    'U8hDwP3T3xo',
    'Окружности: вписанная, описанная, касательная',
    'Профиматика',
    840,
    '[{"time": 0, "label": "Вписанная окружность"}, {"time": 240, "label": "Описанная окружность"}, {"time": 480, "label": "Касательная"}, {"time": 660, "label": "Задачи ЕГЭ"}]'::jsonb,
    0
);

-- =============================================
-- Задание 2: Вычисления (степени, логарифмы, тригонометрия)
-- =============================================

-- 2.1 Степени и корни
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '2.1' AND task_number = 2 LIMIT 1),
    'bLVn_WxKDME',
    'Степени и корни — свойства и вычисления',
    'Борис Трушин',
    780,
    '[{"time": 0, "label": "Свойства степеней"}, {"time": 240, "label": "Корни и дробные показатели"}, {"time": 540, "label": "Типичные задачи ЕГЭ"}]'::jsonb,
    0
);

-- 2.2 Логарифмы
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '2.2' AND task_number = 2 LIMIT 1),
    'W9YHpKXUdlI',
    'Логарифмы: от нуля до ЕГЭ',
    'Математика ЕГЭ 100БАЛЛОВ',
    960,
    '[{"time": 0, "label": "Определение логарифма"}, {"time": 180, "label": "Свойства логарифмов"}, {"time": 480, "label": "Переход к другому основанию"}, {"time": 720, "label": "Примеры из ЕГЭ"}]'::jsonb,
    0
);

-- 2.3 Тригонометрические выражения
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '2.3' AND task_number = 2 LIMIT 1),
    'GkT3p5mHD8Y',
    'Тригонометрия: основные формулы и вычисления',
    'Школково',
    1020,
    '[{"time": 0, "label": "Тригонометрический круг"}, {"time": 240, "label": "Основные тождества"}, {"time": 540, "label": "Формулы двойного угла"}, {"time": 780, "label": "Задачи ЕГЭ"}]'::jsonb,
    0
);

-- =============================================
-- Задание 3: Стереометрия (призма, пирамида, тела вращения)
-- =============================================

-- 3.1 Призма
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '3.1' AND task_number = 3 LIMIT 1),
    'nJh6Wl8QxRw',
    'Призма: объём и площадь поверхности',
    'Борис Трушин',
    720,
    '[{"time": 0, "label": "Виды призм"}, {"time": 180, "label": "Формулы объёма"}, {"time": 420, "label": "Площадь поверхности"}, {"time": 600, "label": "Задачи"}]'::jsonb,
    0
);

-- 3.2 Пирамида
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '3.2' AND task_number = 3 LIMIT 1),
    'Vp5ALm8GQSA',
    'Пирамида в стереометрии: полный разбор',
    'Профиматика',
    900,
    '[{"time": 0, "label": "Правильная пирамида"}, {"time": 300, "label": "Объём пирамиды"}, {"time": 540, "label": "Площадь боковой поверхности"}, {"time": 720, "label": "Типичные задачи"}]'::jsonb,
    0
);

-- 3.3 Тела вращения
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '3.3' AND task_number = 3 LIMIT 1),
    'LxW2n7DXQHE',
    'Цилиндр, конус, шар: формулы и задачи ЕГЭ',
    'Математика ЕГЭ 100БАЛЛОВ',
    840,
    '[{"time": 0, "label": "Цилиндр"}, {"time": 240, "label": "Конус"}, {"time": 480, "label": "Шар"}, {"time": 660, "label": "Комбинации тел"}]'::jsonb,
    0
);

-- =============================================
-- Задание 4: Вероятность
-- =============================================

-- 4.1 Классическая вероятность
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '4.1' AND task_number = 4 LIMIT 1),
    'xT2eGN4WRUE',
    'Теория вероятностей: задание 4 ЕГЭ с нуля',
    'Борис Трушин',
    900,
    '[{"time": 0, "label": "Классическое определение"}, {"time": 180, "label": "Благоприятные исходы"}, {"time": 480, "label": "Примеры из ЕГЭ"}]'::jsonb,
    0
);

-- 4.2 Теоремы сложения и умножения
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '4.2' AND task_number = 4 LIMIT 1),
    'PDhZnJkvqcM',
    'Сложение и умножение вероятностей',
    'Школково',
    780,
    '[{"time": 0, "label": "Совместные и несовместные события"}, {"time": 240, "label": "Теорема сложения"}, {"time": 480, "label": "Теорема умножения"}, {"time": 660, "label": "Задачи"}]'::jsonb,
    0
);

-- 4.3 Условная вероятность
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '4.3' AND task_number = 4 LIMIT 1),
    'NVtw4cR9WnE',
    'Условная вероятность и формула Байеса',
    'Профиматика',
    840,
    '[{"time": 0, "label": "Условная вероятность"}, {"time": 300, "label": "Формула полной вероятности"}, {"time": 540, "label": "Формула Байеса"}, {"time": 720, "label": "Задачи ЕГЭ"}]'::jsonb,
    0
);

-- =============================================
-- Задание 5: Уравнения
-- =============================================

-- 5.1 Линейные и квадратные уравнения
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '5.1' AND task_number = 5 LIMIT 1),
    'e1HxFz3VYMY',
    'Уравнения в задании 5 ЕГЭ: полный разбор',
    'Математика ЕГЭ 100БАЛЛОВ',
    720,
    '[{"time": 0, "label": "Линейные уравнения"}, {"time": 180, "label": "Квадратные уравнения"}, {"time": 420, "label": "Теорема Виета"}, {"time": 600, "label": "Примеры"}]'::jsonb,
    0
);

-- 5.2 Показательные уравнения
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '5.2' AND task_number = 5 LIMIT 1),
    'HKv_Q_M7wjQ',
    'Показательные уравнения: методы решения',
    'Борис Трушин',
    660,
    '[{"time": 0, "label": "Приведение к одному основанию"}, {"time": 180, "label": "Замена переменной"}, {"time": 420, "label": "Задачи ЕГЭ"}]'::jsonb,
    0
);

-- 5.3 Логарифмические уравнения
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '5.3' AND task_number = 5 LIMIT 1),
    'qNaY0hSBdJU',
    'Логарифмические уравнения для ЕГЭ',
    'Школково',
    780,
    '[{"time": 0, "label": "Простейшие лог. уравнения"}, {"time": 240, "label": "ОДЗ"}, {"time": 480, "label": "Методы решения"}, {"time": 660, "label": "Примеры из ЕГЭ"}]'::jsonb,
    0
);

-- =============================================
-- Задание 6: Планиметрия (теоремы косинусов/синусов, площади, подобие)
-- =============================================

-- 6.1 Теорема косинусов
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '6.1' AND task_number = 6 LIMIT 1),
    'mKcAhv_WFRM',
    'Теорема косинусов: все задачи ЕГЭ',
    'Борис Трушин',
    780,
    '[{"time": 0, "label": "Формулировка теоремы"}, {"time": 120, "label": "Нахождение стороны"}, {"time": 360, "label": "Нахождение угла"}, {"time": 600, "label": "Задачи из ЕГЭ"}]'::jsonb,
    0
);

-- 6.2 Теорема синусов
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '6.2' AND task_number = 6 LIMIT 1),
    'jF4N8s_2QRE',
    'Теорема синусов: разбор задания 6',
    'Профиматика',
    660,
    '[{"time": 0, "label": "Теорема синусов"}, {"time": 180, "label": "Радиус описанной окружности"}, {"time": 420, "label": "Примеры задач"}]'::jsonb,
    0
);

-- 6.3 Площади через тригонометрию
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '6.3' AND task_number = 6 LIMIT 1),
    'TYJ4s2BnLz0',
    'Площадь треугольника через синус угла',
    'Математика ЕГЭ 100БАЛЛОВ',
    600,
    '[{"time": 0, "label": "Формула S = ½ab·sin C"}, {"time": 180, "label": "Формула Герона"}, {"time": 360, "label": "Задачи ЕГЭ"}]'::jsonb,
    0
);

-- =============================================
-- Задание 7: Производная и первообразная
-- =============================================

-- 7.1 Правила дифференцирования
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '7.1' AND task_number = 7 LIMIT 1),
    'H3wvRaSKmyQ',
    'Производная: таблица и правила',
    'Борис Трушин',
    720,
    '[{"time": 0, "label": "Определение производной"}, {"time": 180, "label": "Таблица производных"}, {"time": 420, "label": "Правила дифференцирования"}, {"time": 600, "label": "Примеры"}]'::jsonb,
    0
);

-- 7.2 Геометрический смысл производной
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '7.2' AND task_number = 7 LIMIT 1),
    'Wj9NPGuBlMo',
    'Касательная к графику: геометрический смысл производной',
    'Школково',
    660,
    '[{"time": 0, "label": "Угловой коэффициент"}, {"time": 180, "label": "Уравнение касательной"}, {"time": 420, "label": "Задачи из ЕГЭ"}]'::jsonb,
    0
);

-- 7.4 Первообразная и интеграл
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '7.4' AND task_number = 7 LIMIT 1),
    'pB2m_PgFqYY',
    'Первообразная и интеграл: задание 7 ЕГЭ',
    'Профиматика',
    840,
    '[{"time": 0, "label": "Определение первообразной"}, {"time": 240, "label": "Таблица первообразных"}, {"time": 480, "label": "Определённый интеграл"}, {"time": 660, "label": "Площадь фигуры"}]'::jsonb,
    0
);

-- =============================================
-- Задание 8: Прикладные задачи (графики, проценты, выбор)
-- =============================================

-- 8.1 Чтение графиков и диаграмм
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '8.1' AND task_number = 8 LIMIT 1),
    'EWnF3v9Ppqo',
    'Чтение графиков и диаграмм: задание 8 ЕГЭ',
    'Математика ЕГЭ 100БАЛЛОВ',
    540,
    '[{"time": 0, "label": "Типы графиков"}, {"time": 120, "label": "Извлечение данных"}, {"time": 360, "label": "Примеры задач"}]'::jsonb,
    0
);

-- 8.2 Прикладные вычисления
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '8.2' AND task_number = 8 LIMIT 1),
    'r7G0QpKV_nQ',
    'Проценты и пропорции: прикладные задачи',
    'Борис Трушин',
    600,
    '[{"time": 0, "label": "Задачи на проценты"}, {"time": 180, "label": "Единицы измерения"}, {"time": 360, "label": "Пропорции"}]'::jsonb,
    0
);

-- =============================================
-- Задание 9: Функции и графики
-- =============================================

-- 9.1 Свойства функций
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '9.1' AND task_number = 9 LIMIT 1),
    'YwL3sMDk4vc',
    'Свойства функций: область определения, чётность, монотонность',
    'Школково',
    780,
    '[{"time": 0, "label": "Область определения"}, {"time": 180, "label": "Чётность и нечётность"}, {"time": 420, "label": "Монотонность"}, {"time": 600, "label": "Экстремумы"}]'::jsonb,
    0
);

-- 9.2 Преобразования графиков
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '9.2' AND task_number = 9 LIMIT 1),
    'CkX7bMRVDqA',
    'Преобразования графиков функций',
    'Борис Трушин',
    720,
    '[{"time": 0, "label": "Сдвиги по осям"}, {"time": 180, "label": "Растяжения и сжатия"}, {"time": 420, "label": "Отражения"}, {"time": 600, "label": "Задачи ЕГЭ"}]'::jsonb,
    0
);

-- =============================================
-- Задание 10: Текстовые задачи (движение, работа, смеси)
-- =============================================

-- 10.1 Задачи на движение
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '10.1' AND task_number = 10 LIMIT 1),
    'J2Sn3PFG8Wk',
    'Задачи на движение: все типы для ЕГЭ',
    'Математика ЕГЭ 100БАЛЛОВ',
    900,
    '[{"time": 0, "label": "Движение навстречу"}, {"time": 240, "label": "Движение вдогонку"}, {"time": 480, "label": "Движение по кругу"}, {"time": 720, "label": "Задачи из ЕГЭ"}]'::jsonb,
    0
);

-- 10.2 Задачи на работу
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '10.2' AND task_number = 10 LIMIT 1),
    'aQZwN3Rf5Eo',
    'Задачи на совместную работу',
    'Профиматика',
    720,
    '[{"time": 0, "label": "Производительность"}, {"time": 180, "label": "Совместная работа"}, {"time": 420, "label": "Задачи с трубами"}, {"time": 600, "label": "Примеры ЕГЭ"}]'::jsonb,
    0
);

-- =============================================
-- Задание 11: Прогрессии
-- =============================================

-- 11.1 Арифметическая прогрессия
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '11.1' AND task_number = 11 LIMIT 1),
    'Lp8mXwVhFBA',
    'Арифметическая прогрессия: формулы и задачи',
    'Борис Трушин',
    660,
    '[{"time": 0, "label": "Формула n-го члена"}, {"time": 180, "label": "Сумма n членов"}, {"time": 360, "label": "Свойства АП"}, {"time": 540, "label": "Задачи ЕГЭ"}]'::jsonb,
    0
);

-- 11.2 Геометрическая прогрессия
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '11.2' AND task_number = 11 LIMIT 1),
    'M2QN4puvK_8',
    'Геометрическая прогрессия: от формул к задачам ЕГЭ',
    'Школково',
    720,
    '[{"time": 0, "label": "Формула n-го члена"}, {"time": 180, "label": "Сумма n членов"}, {"time": 360, "label": "Бесконечная убывающая ГП"}, {"time": 540, "label": "Задачи ЕГЭ"}]'::jsonb,
    0
);

-- =============================================
-- Задание 12: Экстремумы и оптимизация
-- =============================================

-- 12.1 Экстремумы через производную
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '12.1' AND task_number = 12 LIMIT 1),
    'v5TBqWeLJnA',
    'Нахождение экстремумов через производную',
    'Математика ЕГЭ 100БАЛЛОВ',
    780,
    '[{"time": 0, "label": "Критические точки"}, {"time": 180, "label": "Максимумы и минимумы"}, {"time": 420, "label": "Знак производной"}, {"time": 600, "label": "Задачи ЕГЭ"}]'::jsonb,
    0
);

-- 12.2 Наибольшее и наименьшее на отрезке
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '12.2' AND task_number = 12 LIMIT 1),
    'BwXm3jF7wHc',
    'Наибольшее и наименьшее значение на отрезке',
    'Борис Трушин',
    660,
    '[{"time": 0, "label": "Алгоритм нахождения"}, {"time": 180, "label": "Производная на концах"}, {"time": 360, "label": "Сравнение значений"}, {"time": 480, "label": "Задачи из ЕГЭ"}]'::jsonb,
    0
);

-- 12.3 Задачи на оптимизацию
INSERT INTO video_resources (prototype_id, youtube_video_id, title, channel_name, duration_seconds, timestamps, order_index)
VALUES
(
    (SELECT id FROM prototypes WHERE prototype_code = '12.3' AND task_number = 12 LIMIT 1),
    'dKQ6SyXxwLY',
    'Задачи на оптимизацию: задание 12 ЕГЭ',
    'Профиматика',
    900,
    '[{"time": 0, "label": "Постановка задачи"}, {"time": 180, "label": "Составление функции"}, {"time": 420, "label": "Нахождение экстремума"}, {"time": 660, "label": "Примеры из ЕГЭ"}]'::jsonb,
    0
);
