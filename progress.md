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

### TASK-005 — Подключение Supabase клиента к backend
**Статус:** pending → done
**Дата:** 2026-03-09
**Агент/Сессия:** Claude Opus 4.6
**Summary:** Подключён Supabase клиент к backend. Создан `backend/app/core/config.py` с классом Settings (pydantic-settings), читающим SUPABASE_URL, SUPABASE_SERVICE_KEY, JWT_SECRET из .env. Создан `backend/app/db/supabase_client.py` с функциями get_supabase_client() и verify_connection(). main.py обновлён: lifespan event проверяет подключение при старте, health-check возвращает `{"status": "ok", "db": "connected"|"disconnected"}`. Добавлены зависимости: supabase>=2.0.0, pydantic-settings>=2.0.0, python-dotenv>=1.0.0. 5 тестов проходят, ruff check clean.
**Файлы изменены:**
- backend/app/core/config.py (новый — Settings class)
- backend/app/db/supabase_client.py (новый — Supabase client)
- backend/app/main.py (lifespan event + updated health check)
- backend/pyproject.toml, backend/requirements.txt (новые зависимости)
- backend/tests/test_health.py (обновлён для mock env vars)
- backend/tests/test_supabase_client.py (новый — 3 теста)

**Заметка для следующей итерации:** TASK-005 done → разблокированы: TASK-006 (auth, зависит от TASK-005), TASK-017 (SRS engine, зависит от TASK-005), TASK-036 (import script, зависит от TASK-005). Следующие приоритетные critical задачи с выполненными зависимостями: TASK-004 (RLS + seeds, dep: TASK-003 ✅), TASK-006 (auth, dep: TASK-005 ✅), TASK-010 (frontend layout, dep: TASK-001 ✅), TASK-013 (MathRenderer, dep: TASK-001 ✅). TASK-006 — наиболее критичная, разблокирует TASK-007/008/009/011. Singleton Supabase client через global _client. Тесты используют mock env vars через patch.dict(os.environ).

### TASK-006 — Backend: аутентификация (регистрация, вход, выход через Supabase Auth)
**Статус:** pending → done
**Дата:** 2026-03-09
**Агент/Сессия:** Claude Opus 4.6
**Summary:** Реализована полная аутентификация через Supabase Auth. Создан `app/core/auth.py` с dependency `get_current_user` для JWT-верификации (HS256, audience="authenticated"). Создан `app/routers/auth.py` с эндпоинтами: POST /auth/register (регистрация + создание users row), POST /auth/login (вход по email/password), POST /auth/logout (sign_out). Создан `app/routers/users.py` с GET /api/users/me (профиль пользователя с JWT-защитой). Pydantic-схемы в `app/models/auth.py`: RegisterRequest, LoginRequest, AuthResponse, UserProfile. Добавлены зависимости: email-validator. 14 тестов (9 auth + 2 health + 3 supabase), ruff clean.
**Файлы изменены:**
- backend/app/core/auth.py (новый — JWT verification, get_current_user dependency)
- backend/app/models/auth.py (новый — Pydantic schemas)
- backend/app/routers/auth.py (новый — register, login, logout endpoints)
- backend/app/routers/users.py (новый — GET /api/users/me)
- backend/app/main.py (включены auth + users роутеры)
- backend/pyproject.toml, backend/requirements.txt (email-validator)
- backend/tests/test_auth.py (новый — 9 тестов)

**Заметка для следующей итерации:** TASK-006 done → разблокированы: TASK-007 (user profile API, dep: TASK-006 ✅), TASK-008 (topics API, dep: TASK-006 ✅ + TASK-004), TASK-009 (problems API, dep: TASK-006 ✅ + TASK-004), TASK-011 (frontend auth, dep: TASK-010 + TASK-006 ✅). Следующие приоритетные critical задачи: TASK-004 (RLS + seeds), TASK-007 (user profile), TASK-010 (frontend layout), TASK-013 (MathRenderer), TASK-017 (SRS engine). Важно: supabase-py v2 использует `supabase_auth.errors.AuthApiError` (не `gotrue`). JWT secret из Supabase — используется для верификации токенов с audience="authenticated". GET /api/users/me уже реализован базово — TASK-007 добавит PATCH и /stats.

### TASK-004 — Настройка RLS-политик и seed-данные для topics
**Статус:** pending → done
**Дата:** 2026-03-09
**Агент/Сессия:** Claude Opus 4.6
**Summary:** Создана миграция `supabase/migrations/002_rls_and_seeds.sql`. RLS включён на всех 10 таблицах. Пользовательские таблицы (users, user_problem_attempts, srs_cards, user_topic_progress, user_sessions, user_daily_activity) — полные CRUD-политики с `auth.uid() = user_id/id`. Справочные таблицы (topics, theory_content, problems, topic_relationships) — SELECT для всех authenticated. Seed: 19 записей в topics с task_number 1–19, названиями из ЕГЭ, описаниями, difficulty_level, max_points (1 для 1–12, 2 для 13–15, 3 для 16–17, 4 для 18–19), estimated_study_hours. Ruff clean, 14 тестов pass.
**Файлы изменены:**
- supabase/migrations/002_rls_and_seeds.sql (новый — RLS + seeds)
- tasks.json (TASK-004 status → done)

**Заметка для следующей итерации:** TASK-004 done → разблокированы: TASK-008 (topics API, dep: TASK-006 ✅ + TASK-004 ✅), TASK-009 (problems API, dep: TASK-006 ✅ + TASK-004 ✅), TASK-016 (seed problems, dep: TASK-004 ✅), TASK-032 (seed theory, dep: TASK-004 ✅). Следующие приоритетные critical задачи с выполненными зависимостями: TASK-007 (user profile, dep: TASK-006 ✅), TASK-008 (topics API), TASK-009 (problems API), TASK-010 (frontend layout, dep: TASK-001 ✅), TASK-013 (MathRenderer, dep: TASK-001 ✅), TASK-017 (SRS engine, dep: TASK-005 ✅). TASK-007/008/009 — наиболее критичные для разблокировки UI-задач.
