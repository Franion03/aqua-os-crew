# AquaOS — Microservices Architecture

Water polo club management platform split into four independent services.

```
┌──────────────────────────────────────────────────────────────┐
│                        Client Layer                           │
│  ┌─────────────────────┐  ┌─────────────────────────────┐   │
│  │  aqua-os-web        │  │  aqua-os-app (Flutter)       │   │
│  │  TypeScript + React │  │  Android / iOS / Web         │   │
│  │  Tailwind CSS       │  │  Trainer & Player dashboards │   │
│  └─────────┬───────────┘  └──────────────┬──────────────┘   │
└────────────┼──────────────────────────────┼──────────────────┘
             │                              │
             ▼                              ▼
┌─────────────────────────┐  ┌────────────────────────────────┐
│  aqua-os-backend (Go)   │  │  aqua-os-crew (Python)         │
│  chi router             │  │  FastAPI + CrewAI              │
│  SQLite                 │  │  OpenRouter / Gemini           │
│  Port :8080             │  │  Port :8001                    │
└─────────────────────────┘  └────────────────────────────────┘
```

## Services

### aqua-os-backend (`/mnt/SecondDrive/github/aqua-os-backend`)

Go REST API with chi router + SQLite.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/levels` | All 7 training levels |
| `GET` | `/api/levels/{id}` | Level + exercises |
| `POST` | `/api/exercises` | Add exercise |
| `GET` | `/api/exercises` | List exercises |
| `DELETE` | `/api/exercises/{id}` | Remove exercise |

**Run:** `go run ./cmd/server` or `make run`

### aqua-os-web (`/mnt/SecondDrive/github/aqua-os-web`)

TypeScript + React + Vite + Tailwind CSS. Fully responsive (mobile sidebar, touch targets >= 44px, glass-morphism dark theme).

**Run:** `npm run dev` → http://localhost:5173 (proxies `/api` to `:8080`)

### aqua-os-crew (`/mnt/SecondDrive/github/aqua-os-crew`)

Python CrewAI microservice. 5 agent crews: match prep, enrollment, progress review, season plan, injury response.

**Run:** `pip install -r requirements.txt && uvicorn main:app --port 8001`

### aqua-os-app (`/mnt/SecondDrive/github/aqua_os_app`)

Flutter mobile app for trainers and players.

**Screens:** Splash → Login → Role Selection → Trainer/Player Dashboard → Availability, Feedback, Attendance

**Run:** `flutter run`

## Original Project

The original monolithic `aqua-os` at `/mnt/SecondDrive/github/aqua-os` is preserved. This contains the Python FastAPI backend + React JSX frontend + CrewAI agents all in one repo — kept as working reference.
