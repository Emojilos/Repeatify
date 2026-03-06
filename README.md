# Repeatify

Умный тренажёр для подготовки к ЕГЭ по математике на основе интервального повторения (FSRS) и графа знаний (FIRe).

## Структура проекта

```
repeatify/
├── frontend/          # React SPA (Vite + Tailwind CSS + HashRouter)
│   ├── public/
│   │   └── 404.html  # SPA redirect для GitHub Pages
│   ├── src/
│   └── .env.example
├── backend/           # Python FastAPI (FSRS engine, FIRe propagator)
│   ├── app/
│   └── .env.example
├── database/
│   ├── migrations/    # SQL миграции Supabase
│   └── seeds/         # Seed-данные (topics, cards)
└── .github/
    └── workflows/     # CI/CD (deploy frontend, keep-alive)
```

## Быстрый старт

### Frontend
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

### Backend
```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Переменные окружения

- `frontend/.env.example` — VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL
- `backend/.env.example` — SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET, ALLOWED_ORIGINS
