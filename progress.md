# Progress Log — Repeatify

Лог прогресса агентов по задачам из tasks.json.

---

## Формат записи

```
### TASK-XXX — Краткое описание
**Статус:** pending → done
**Дата:** YYYY-MM-DD
**Агент/Сессия:** ID или описание
**Summary:** Что было сделано
**Файлы изменены:** список файлов
```

---

<!-- Агенты добавляют записи ниже этой линии -->

### TASK-002 — Инициализация backend (FastAPI + Python)
**Статус:** pending → done
**Дата:** 2026-03-09
**Агент/Сессия:** Claude Opus 4.6
**Summary:** Создан backend-проект с FastAPI. Структура: app/main.py, app/routers/, app/models/, app/services/, app/core/, app/db/. Health-check GET /health возвращает {"status": "ok"}. CORS настроен для localhost:5173. Swagger UI доступен на /docs. Uvicorn запускается без ошибок. Ruff check и pytest проходят (2 теста).
**Файлы изменены:**
- backend/pyproject.toml
- backend/requirements.txt
- backend/app/__init__.py, routers/__init__.py, models/__init__.py, services/__init__.py, core/__init__.py, db/__init__.py
- backend/app/main.py
- backend/tests/__init__.py, tests/test_health.py

**Заметка для следующей итерации:** Следующие приоритетные задачи без зависимостей: TASK-001 (frontend init) и TASK-003 (Supabase schema). TASK-005 (Supabase client подключение к backend) зависит от TASK-002 (done) + TASK-003 (pending). Python версия 3.14.3 используется через uv.

### TASK-003 — Настройка Supabase: создание схемы БД
**Статус:** pending → done
**Дата:** 2026-03-09
**Агент/Сессия:** Claude Opus 4.6
**Summary:** Создана SQL-миграция `supabase/migrations/001_initial_schema.sql` с полной схемой БД. 8 ENUM-типов (difficulty_level, problem_difficulty, content_type, card_type, card_status, session_type, self_assessment, relationship_type). 10 таблиц (users, topics, theory_content, problems, user_problem_attempts, srs_cards, user_topic_progress, user_sessions, user_daily_activity, topic_relationships). 4 индекса для критических запросов. Все FK-связи, CHECK-ограничения, UNIQUE-constraints и default-значения установлены по PRD. Создан `.env.example` с переменными SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY, JWT_SECRET.
**Файлы изменены:**
- supabase/migrations/001_initial_schema.sql
- .env.example

**Заметка для следующей итерации:** TASK-003 done → разблокированы: TASK-004 (RLS + seeds, зависит от TASK-003), TASK-005 (Supabase client, зависит от TASK-002 done + TASK-003 done). Следующие приоритетные задачи: TASK-001 (frontend init, без зависимостей), TASK-004 (RLS + seeds), TASK-005 (Supabase client). Ruff check и pytest проходят. Примечание: в PRD два разных enum для difficulty — difficulty_level (basic/medium/hard) для topics и problem_difficulty (basic/medium/hard/olympiad) для problems.

### TASK-001 — Инициализация frontend (Vite + React + TypeScript + Tailwind CSS)
**Статус:** pending → done
**Дата:** 2026-03-09
**Агент/Сессия:** Claude Opus 4.6
**Summary:** Создан frontend-проект через Vite (react-ts шаблон). React 19 + TypeScript 5.9. Tailwind CSS v4 установлен и настроен через `@tailwindcss/vite` плагин. Структура папок: src/components, src/pages, src/stores, src/lib, src/types. HashRouter из react-router-dom v7 настроен со всеми маршрутами из acceptance criteria (/, /auth/login, /auth/register, /dashboard, /topics, /topics/:id, /topics/:id/fire, /practice, /practice/session, /practice/results, /progress, /profile). Все страницы-заглушки созданы. Dashboard показывает "Repeatify" с классом text-blue-500 (Tailwind работает). `npm run build` проходит без ошибок. `npm run dev` запускается.
**Файлы изменены:**
- frontend/package.json (Vite + React + Tailwind + react-router-dom)
- frontend/vite.config.ts (Tailwind v4 plugin)
- frontend/src/index.css (Tailwind import)
- frontend/src/main.tsx, frontend/src/App.tsx (HashRouter setup)
- frontend/src/pages/ (11 stub pages: Dashboard, Login, Register, Topics, TopicDetail, TopicFire, Practice, PracticeSession, PracticeResults, Progress, Profile)

**Заметка для следующей итерации:** TASK-001 done → разблокированы: TASK-010 (layout + routing, зависит от TASK-001), TASK-013 (MathRenderer, зависит от TASK-001), TASK-033 (CI/CD GitHub Pages, зависит от TASK-001 + TASK-010). Все 3 infrastructure-задачи (TASK-001, TASK-002, TASK-003) теперь done. Следующие приоритетные critical задачи: TASK-004 (RLS + seeds), TASK-005 (Supabase client). Примечание: используется Tailwind CSS v4 (без tailwind.config.js — конфигурация через CSS и @tailwindcss/vite плагин), React 19 (не 18), react-router-dom v7.
