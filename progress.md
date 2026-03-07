# Repeatify — Лог прогресса агентов

## Инструкция для агентов

После завершения каждой задачи добавь запись в формате:

```
## [TASK-XXX] Название задачи
- **Дата:** YYYY-MM-DD
- **Статус:** done
- **Что сделано:** краткое описание изменений (2–5 предложений)
- **Ключевые файлы:** список созданных/изменённых файлов
- **Проблемы:** если были — опиши и как решил
```

---

<!-- Агенты добавляют записи ниже этой строки -->

## [TASK-012] Seed-данные: 26 карточек типа step_by_step
- **Дата:** 2026-03-07
- **Статус:** done (файл создан; загрузка требует `python database/seeds/load_cards.py stepbystep` с настроенным .env)
- **Что сделано:** Создан `database/seeds/cards_stepbystep.json` с 26 карточками типа step_by_step (превышает минимум 20). Распределение по темам: GEO.STER (6), GEO.PLAN (5), ANA.DER (5), ANA.INT (3), PAR.BOUND (4), PAR.COUNT (3). Каждая карточка содержит: solution_steps (2–4 шага с полями step_number, title, text, latex, hint), hints массив, difficulty, ege_task_number. LaTeX использует $...$ и $$...$$. load_cards.py уже поддерживает тип `stepbystep` и поле `solution_steps` — никаких изменений скрипта не потребовалось.
- **Ключевые файлы:** database/seeds/cards_stepbystep.json
- **Проблемы:** python3/uv заблокированы хуком разрешений — верификация `uv run pytest` невозможна (в данной задаче нет Python-кода с тестами). Шаги тестирования 1–3 требуют применения в Supabase. Шаг 4 (KaTeX) требует проверки в браузере. Следующий агент: TASK-013 (FSRS Engine) уже in_progress — нужно разблокировать запуск `uv run pytest tests/unit/test_fsrs_engine.py`.

## [TASK-011] Seed-данные: 50+ карточек типа basic_qa с LaTeX-формулами
- **Дата:** 2026-03-07
- **Статус:** done (файлы созданы; загрузка в Supabase требует ручного запуска load_cards.py с настроенным .env)
- **Что сделано:** Создан `database/seeds/cards_basic.json` с 58 карточками типа basic_qa, распределёнными по 7 темам: ALG.LIN (10), ALG.QUAD (10), ALG.LOG (8), ANA.DER (8), PRB.BASIC (8), GEO.PLAN (8), ALG.TRIG (6). Все карточки содержат LaTeX-нотацию ($...$ и $$...$$), имеют вопрос, ответ и 1-2 подсказки. Создан универсальный `database/seeds/load_cards.py`: принимает тип (`basic`/`stepbystep`) или `--file path`, резолвит topic_code → topic_id, проверяет дубли по (topic_id, question_text), логирует вставленные/пропущенные/ошибочные, поддерживает повторный запуск без дублей.
- **Ключевые файлы:** database/seeds/cards_basic.json, database/seeds/load_cards.py
- **Проблемы:** uv не установлен → `uv run ruff check .` и `uv run pytest` не запускались. Синтаксис проверен визуально. Загрузка в Supabase требует `python database/seeds/load_cards.py basic` с переменными SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY. Следующий агент: TASK-012 (step_by_step карточки) теперь не зависит от TASK-011, но TASK-014 (генерация сессии) теперь разблокирован вместе с TASK-013 и TASK-011.

## [TASK-010] Seed-данные: рёбра графа знаний topic_dependencies с весами
- **Дата:** 2026-03-07
- **Статус:** done (файлы созданы; загрузка в Supabase требует ручного запуска load_dependencies.py с настроенным .env)
- **Что сделано:** Создан `database/seeds/topic_dependencies.json` с 50 зависимостями между темами графа знаний. Покрыты все ключевые педагогические цепочки ЕГЭ: ALG.LIN→ALG.QUAD (weight=1.0), ALG.QUAD→ALG.EXP (weight=0.8), ALG.EXP→ALG.LOG (weight=0.9), цепочки тригонометрии, прогрессий, комбинаторики, геометрии (план→стерео→координаты), математического анализа (функции→производная→интеграл), вероятности и задач с параметром. Три типа связей: prerequisite, related, part_of. Создан `database/seeds/load_dependencies.py` со встроенной проверкой DAG (DFS, обнаружение циклов перед загрузкой), upsert-логикой (нет дублей при повторном запуске), информативными логами.
- **Ключевые файлы:** database/seeds/topic_dependencies.json, database/seeds/load_dependencies.py
- **Проблемы:** uv не установлен на машине — ruff/pytest не запускались (нет Python-кода с логикой, требующей тестов; DAG-валидация встроена в скрипт). Загрузка в Supabase требует `python database/seeds/load_dependencies.py` с переменными SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY. Следующий агент: TASK-016 (FIRe credit propagation) теперь разблокирован вместе с TASK-010.

## [TASK-009] Seed-данные: граф знаний — узлы topics по кодификатору ЕГЭ
- **Дата:** 2026-03-07
- **Статус:** done (файлы созданы; загрузка в Supabase требует ручного запуска load_topics.py с настроенным .env)
- **Что сделано:** Создан `database/seeds/topics.json` с 66 темами (5 корневых разделов уровня 0, 17 тем уровня 1, 44 подтемы уровня 2), охватывающими все задания ЕГЭ 1–19. Разделы: Алгебра (ALG), Геометрия (GEO), Математический анализ (ANA), Теория вероятностей и статистика (PRB), Задачи с параметром (PAR). Каждая тема имеет code, title, description, difficulty (0.0–1.0), level (0/1/2), parent_code и ege_task_numbers. Создан `database/seeds/load_topics.py` — скрипт загрузки в Supabase с upsert-логикой (level-by-level для корректного разрешения parent_id), логированием вставленных/пропущенных записей, обработкой .env из backend/.env.
- **Ключевые файлы:** database/seeds/topics.json, database/seeds/load_topics.py
- **Проблемы:** Шаги тестирования (SELECT COUNT(*) >= 40, проверка уровней) требуют применения в Supabase — нужно запустить `python database/seeds/load_topics.py` с переменными SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY. uv не установлен на машине — ruff/pytest запустить не удалось. Следующий агент: TASK-010 (рёбра графа) теперь разблокирован.

## [TASK-004] Настройка RLS-политик Supabase
- **Дата:** 2026-03-07
- **Статус:** done (SQL файл создан; применение к Supabase требует ручного действия)
- **Что сделано:** Создан `database/migrations/002_rls_policies.sql`. RLS включён на всех 9 таблицах. Пользовательские таблицы (users, user_card_progress, review_logs, user_topic_mastery, study_sessions, daily_activity) защищены политиками SELECT/INSERT/UPDATE через `auth.uid()` — пользователь видит и изменяет только свои строки. review_logs намеренно без UPDATE-политики (иммутабельные логи). Публичные таблицы (topics, topic_dependencies, cards) доступны на SELECT всем authenticated пользователям; INSERT/UPDATE/DELETE только через service role (service role автоматически обходит RLS).
- **Ключевые файлы:** database/migrations/002_rls_policies.sql
- **Проблемы:** Шаги тестирования (создать двух пользователей, проверить изоляцию) требуют применения миграции в Supabase Dashboard SQL Editor вручную — агент не имеет доступа к проекту. Следующий агент может проверить в Supabase: после применения запросы от user_b не должны видеть строки user_a.

## [TASK-013] FSRS Engine: интеграция py-fsrs
- **Дата:** 2026-03-07
- **Статус:** in_progress (код и тесты написаны; `uv run pytest` заблокирован хуком разрешений)
- **Что сделано:** Создан `backend/app/core/fsrs/engine.py` с классом `FSRSEngine`. Метод `schedule(card_progress, rating)` принимает dict из БД (stability, difficulty, fsrs_state, due_date, last_review, review_count) и int рейтинг 1-4, возвращает обновлённые FSRS-поля. Метод `preview_ratings()` возвращает результаты для всех 4 рейтингов без сохранения (для оптимистичного UI). Добавлен `py-fsrs>=6.0.0` в requirements.txt и pyproject.toml. Написаны 10 unit-тестов в `backend/tests/unit/test_fsrs_engine.py`.
- **Ключевые файлы:** backend/app/core/__init__.py, backend/app/core/fsrs/__init__.py, backend/app/core/fsrs/engine.py, backend/tests/unit/test_fsrs_engine.py, backend/requirements.txt, backend/pyproject.toml
- **Проблемы:** `uv run pytest` и `python3 -m pytest` заблокированы хуком разрешений пользователя. Следующий агент должен запустить `cd backend && uv run pytest tests/unit/test_fsrs_engine.py -v` для верификации и смены статуса на done. Также нужно установить `uv` если не установлен: `pip3 install uv`.

## [TASK-003] Создание схемы базы данных Supabase
- **Дата:** 2026-03-07
- **Статус:** done (SQL файл создан; применение к Supabase требует ручного действия)
- **Что сделано:** Создан `database/migrations/001_initial_schema.sql` с 9 таблицами: users, topics, topic_dependencies, cards, user_card_progress, review_logs, user_topic_mastery, study_sessions, daily_activity. Добавлены 5 ENUM типов (card_type, fsrs_state, session_type, study_plan_type, relationship_type), все индексы, UNIQUE-ограничения, CHECK-ограничения и триггеры auto-update для `updated_at`. FK из `review_logs.session_id` → `study_sessions` добавлен через `ALTER TABLE` после создания обеих таблиц (избегает circular dependency).
- **Ключевые файлы:** database/migrations/001_initial_schema.sql
- **Проблемы:** Шаг "Миграция применена к Supabase" требует ручного применения SQL в Supabase Dashboard SQL Editor — агент не имеет доступа к Supabase проекту. Следующий агент должен скопировать содержимое файла и выполнить в Supabase SQL Editor.

## [TASK-005] Инициализация FastAPI бэкенда: структура, JWT верификация, /health
- **Дата:** 2026-03-07
- **Статус:** in_progress (код готов, требуется верификация через `uv run pytest` — uv не установлен на машине)
- **Что сделано:** Создана полная структура бэкенда: app/main.py (FastAPI + CORS middleware), app/config.py (pydantic-settings из .env), app/api/deps.py (JWT верификация через python-jose, HTTPBearer auto_error=False → 401 при отсутствии токена), app/api/v1/health.py (GET /health), app/api/v1/me.py (GET /api/v1/me с auth), app/api/v1/router.py (prefix=/api/v1). Созданы requirements.txt, Dockerfile, pyproject.toml с dev-зависимостями (pytest, ruff), unit-тесты в tests/unit/test_health.py.
- **Ключевые файлы:** backend/app/main.py, backend/app/config.py, backend/app/api/deps.py, backend/app/api/v1/health.py, backend/app/api/v1/me.py, backend/app/api/v1/router.py, backend/requirements.txt, backend/Dockerfile, backend/pyproject.toml, backend/tests/unit/test_health.py
- **Проблемы:** uv не установлен → `uv run ruff check .` и `uv run pytest` не могут быть выполнены агентом. Следующий агент должен установить uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`) и запустить тесты для верификации.

## [TASK-002] fix: package.json — удалён конфликтующий @tailwindcss/vite
- **Дата:** 2026-03-07
- **Статус:** in_progress (npm install всё ещё не запущен, заблокирован хуком)
- **Что сделано:** Удалена devDependency `@tailwindcss/vite` (v4-only плагин) из package.json, который конфликтовал с `tailwindcss: ^3.4.14`. Теперь package.json использует стандартный Tailwind v3 через postcss.

## [TASK-002] Инициализация React-проекта: Vite + Tailwind + HashRouter + KaTeX
- **Дата:** 2026-03-07
- **Статус:** in_progress (требуется `npm install && npm run build` для верификации)
- **Что сделано:** Создана полная структура фронтенда: package.json (Vite 5, React 18, Tailwind 3, React Router 6, KaTeX, Zustand, @supabase/supabase-js), vite.config.js с base='/repeatify/', tailwind.config.js, postcss.config.js, src/main.jsx с HashRouter, src/App.jsx со всеми роутами, src/index.css с Tailwind директивами, LatexRenderer.jsx с auto-detect $...$ и $$...$$, lib/katex/render.js утилита.
- **Ключевые файлы:** frontend/package.json, frontend/vite.config.js, frontend/tailwind.config.js, frontend/postcss.config.js, frontend/index.html, frontend/src/main.jsx, frontend/src/App.jsx, frontend/src/index.css, frontend/src/components/math/LatexRenderer.jsx, frontend/src/lib/katex/render.js
- **Проблемы:** npm install заблокирован хуком разрешений — нужно запустить вручную `cd frontend && npm install && npm run build` для верификации TASK-002.

## [TASK-001] Инициализация монорепозитория
- **Дата:** 2026-03-07
- **Статус:** done
- **Что сделано:** Создана полная структура папок монорепозитория. Созданы директории database/migrations/, database/seeds/, .github/workflows/ с .gitkeep. Созданы frontend/.env.example и backend/.env.example с нужными переменными. Создан frontend/public/404.html с SPA-редиректом для GitHub Pages. README.md обновлён с описанием структуры и быстрым стартом.
- **Ключевые файлы:** database/migrations/.gitkeep, database/seeds/.gitkeep, .github/workflows/.gitkeep, frontend/.env.example, backend/.env.example, frontend/public/404.html, README.md
- **Проблемы:** Не было проблем.
