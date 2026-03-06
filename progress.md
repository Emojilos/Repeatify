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
