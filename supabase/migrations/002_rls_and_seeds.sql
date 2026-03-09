-- ============================================================================
-- 002_rls_and_seeds.sql
-- Repeatify: RLS policies for all tables + seed data for topics (19 ЕГЭ tasks)
-- ============================================================================

-- ============================================================================
-- ENABLE RLS ON ALL TABLES
-- ============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE theory_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE problems ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_problem_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE srs_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_topic_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_daily_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_relationships ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES: users
-- Users can only access/modify their own record
-- ============================================================================

CREATE POLICY "users_select_own" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "users_insert_own" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "users_update_own" ON users
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

CREATE POLICY "users_delete_own" ON users
    FOR DELETE USING (auth.uid() = id);

-- ============================================================================
-- RLS POLICIES: topics (read-only for all authenticated users)
-- ============================================================================

CREATE POLICY "topics_select_authenticated" ON topics
    FOR SELECT TO authenticated
    USING (true);

-- ============================================================================
-- RLS POLICIES: theory_content (read-only for all authenticated users)
-- ============================================================================

CREATE POLICY "theory_content_select_authenticated" ON theory_content
    FOR SELECT TO authenticated
    USING (true);

-- ============================================================================
-- RLS POLICIES: problems (read-only for all authenticated users)
-- ============================================================================

CREATE POLICY "problems_select_authenticated" ON problems
    FOR SELECT TO authenticated
    USING (true);

-- ============================================================================
-- RLS POLICIES: topic_relationships (read-only for all authenticated users)
-- ============================================================================

CREATE POLICY "topic_relationships_select_authenticated" ON topic_relationships
    FOR SELECT TO authenticated
    USING (true);

-- ============================================================================
-- RLS POLICIES: user_problem_attempts
-- Users can only access/modify their own attempts
-- ============================================================================

CREATE POLICY "user_problem_attempts_select_own" ON user_problem_attempts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "user_problem_attempts_insert_own" ON user_problem_attempts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_problem_attempts_update_own" ON user_problem_attempts
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_problem_attempts_delete_own" ON user_problem_attempts
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- RLS POLICIES: srs_cards
-- Users can only access/modify their own cards
-- ============================================================================

CREATE POLICY "srs_cards_select_own" ON srs_cards
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "srs_cards_insert_own" ON srs_cards
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "srs_cards_update_own" ON srs_cards
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "srs_cards_delete_own" ON srs_cards
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- RLS POLICIES: user_topic_progress
-- Users can only access/modify their own progress
-- ============================================================================

CREATE POLICY "user_topic_progress_select_own" ON user_topic_progress
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "user_topic_progress_insert_own" ON user_topic_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_topic_progress_update_own" ON user_topic_progress
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_topic_progress_delete_own" ON user_topic_progress
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- RLS POLICIES: user_sessions
-- Users can only access/modify their own sessions
-- ============================================================================

CREATE POLICY "user_sessions_select_own" ON user_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "user_sessions_insert_own" ON user_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_sessions_update_own" ON user_sessions
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_sessions_delete_own" ON user_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- RLS POLICIES: user_daily_activity
-- Users can only access/modify their own activity records
-- ============================================================================

CREATE POLICY "user_daily_activity_select_own" ON user_daily_activity
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "user_daily_activity_insert_own" ON user_daily_activity
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_daily_activity_update_own" ON user_daily_activity
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "user_daily_activity_delete_own" ON user_daily_activity
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- SEED DATA: topics — 19 типов заданий ЕГЭ по математике (профиль)
-- ============================================================================
-- Баллы: задания 1–12 (Часть 1) = 1 балл каждое
--         задания 13–15 = 2 балла каждое
--         задания 16–17 = 3 балла каждое
--         задания 18–19 = 4 балла каждое
-- ============================================================================

INSERT INTO topics (task_number, title, description, difficulty_level, max_points, estimated_study_hours, order_index) VALUES
(1,  'Планиметрия (базовая)',
     'Вычисления длин, площадей, углов в плоских фигурах. Треугольники, четырёхугольники, окружности.',
     'basic', 1, 6, 1),

(2,  'Вычисления и преобразования',
     'Числовые выражения, степени, корни, логарифмы. Рациональные и иррациональные выражения.',
     'basic', 1, 4, 2),

(3,  'Стереометрия (базовая)',
     'Объёмы и площади поверхностей: призма, пирамида, цилиндр, конус, шар.',
     'basic', 1, 6, 3),

(4,  'Теория вероятностей',
     'Классическая вероятность, формула сложения и умножения, условная вероятность, независимые события.',
     'basic', 1, 5, 4),

(5,  'Уравнения',
     'Линейные, квадратные, рациональные, иррациональные, показательные, логарифмические, тригонометрические уравнения.',
     'basic', 1, 8, 5),

(6,  'Планиметрия (вычислительная)',
     'Вычисления в треугольниках и четырёхугольниках: теоремы синусов и косинусов, вписанные/описанные окружности, площади.',
     'medium', 1, 8, 6),

(7,  'Производная и первообразная',
     'Геометрический и физический смысл производной. Касательная. Экстремумы. Первообразная и интеграл.',
     'medium', 1, 10, 7),

(8,  'Прикладные задачи',
     'Текстовые задачи на движение, работу, сплавы, проценты, прогрессии.',
     'medium', 1, 8, 8),

(9,  'Функции и графики',
     'Свойства функций: область определения, чётность, монотонность, экстремумы. Преобразования графиков.',
     'medium', 1, 6, 9),

(10, 'Текстовые задачи',
     'Задачи на составление уравнений: движение, работа, смеси, проценты, числовые задачи.',
     'medium', 1, 8, 10),

(11, 'Последовательности и прогрессии',
     'Арифметическая и геометрическая прогрессии. Суммы, n-й член, свойства.',
     'medium', 1, 5, 11),

(12, 'Наибольшее и наименьшее значение',
     'Нахождение наибольшего/наименьшего значения функции на отрезке с помощью производной.',
     'medium', 1, 6, 12),

(13, 'Стереометрия (профильная)',
     'Углы и расстояния в пространстве. Сечения многогранников. Комбинации тел.',
     'hard', 2, 15, 13),

(14, 'Неравенства',
     'Рациональные, показательные, логарифмические неравенства. Метод интервалов. Системы неравенств.',
     'hard', 2, 12, 14),

(15, 'Финансовая математика',
     'Кредиты, вклады, оптимизация платежей. Аннуитетные и дифференцированные схемы.',
     'hard', 2, 10, 15),

(16, 'Планиметрия (профильная)',
     'Доказательство и вычисление в планиметрии: окружности, вписанные углы, подобие, площади.',
     'hard', 3, 18, 16),

(17, 'Параметры',
     'Уравнения и неравенства с параметром. Графический метод. Исследование количества решений.',
     'hard', 3, 20, 17),

(18, 'Числа и их свойства',
     'Делимость, остатки, НОД, НОК. Диофантовы уравнения. Числовые задачи с целыми числами.',
     'hard', 4, 15, 18),

(19, 'Комбинаторика и логика',
     'Комбинаторные задачи, принцип Дирихле, раскраски, игровые стратегии, логические задачи.',
     'hard', 4, 15, 19);
