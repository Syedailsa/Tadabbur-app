# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tadabbur is an AI-powered Quranic insights app. It's a monorepo with a **Next.js 16 frontend** and a **FastAPI backend**, communicating primarily over WebSockets for real-time AI responses.

## Commands

### Frontend (`frontend/`)
```bash
npm install        # Install dependencies
npm run dev        # Dev server (Turbopack) at http://localhost:3000
npm run build      # Production build
npm run lint       # ESLint
```

### Backend (`backend/`)
```bash
uv sync                          # Install dependencies (uses uv, not pip)
uvicorn main:app --reload        # Dev server at http://localhost:8000
pytest tests/                    # Run tests
pytest tests/test_main.py -k "test_name"  # Run single test
```

## Architecture

### Communication Model
The frontend and backend communicate via **WebSockets** (not REST) for the core chat flow. The frontend sends typed `OutgoingMessageType` messages; the backend streams back typed `WebSocketMessageType` responses. Both type sets are defined in `frontend/app/utils/types.ts`.

Key WebSocket flows:
- `session-init` → backend initializes a LangGraph agent session
- `user_message` → backend streams `assistance_response`, `loading_message`, `open_audio_dialog`, `open_verse_dialog`, `tts_audio_chunk`
- REST endpoints handle auth, bookmarks, profile, and file uploads

### Backend (`backend/`)
- **`main.py`** — FastAPI app entry point. Contains WebSocket handlers, session management, JWT auth middleware, CORS config, and startup/shutdown lifespan (database pool init). Very large file (~81KB).
- **`tadabbur_agents/agent.py`** — Core LangGraph tafseer agent. Orchestrates tool calls for Quran lookups, embeddings, and LLM responses.
- **`tadabbur_agents/story_agent.py`** — Story mode agent (developer-only feature).
- **`api/`** — FastAPI routers split by domain (auth, quran, reflection, password reset, etc.).
- **`data/database.py`** — AsyncPG connection pool setup and table creation on startup.
- **`utils/authentication.py`** — JWT creation/verification, bcrypt password hashing, Google OAuth token verification.
- **`config/db.py`** — Supabase client initialization.

Database is **PostgreSQL via Supabase** (asyncpg pool, min 5 / max 20 connections). Vector embeddings are stored in **Qdrant**.

### Frontend (`frontend/app/`)
- **`pages/auth/`** — Login, signup, password reset (Google OAuth + email/password).
- **`pages/chatbot/page.tsx`** — Main chat interface.
- **`components/chatbot/UI/`** — All chat UI components: message list, history drawer, model selector, prompt options, story mode, report dialog.
- **`context/chatbot/ChatContext.tsx`** — Global chat state: messages, history, selected model, WebSocket ref, file uploads, dialogs.
- **`providers/chatbot/ChatProvider.tsx`** — Wraps context with side effects and WebSocket lifecycle.
- **`utils/types.ts`** — Single source of truth for all TypeScript types across the app.

Auth uses JWT tokens stored in both `js-cookie` (7-day expiry) and `localStorage`.

### Environment Variables
Frontend (`.env`): `NEXT_PUBLIC_GOOGLE_CLIENT_ID`, `NEXT_PUBLIC_WEBSOCKET_URL`, `NEXT_PUBLIC_BACKEND_URL`

Backend (`.env`): `DATABASE_URL`, `JWT_SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `QDRANT_API_KEY`, `QDRANT_URL_ENDPOINT`, `GROQ_AI_API_KEY`, `FIREWORKS_AI_API_KEY`, `MURF_AI_API_KEY`, `FRONTEND_URL`, `WEB_GOOGLE_CLIENT_ID`

## Git Workflow
- `main` is protected — PRs required, 1 approval, linear history (squash and merge)
- Branch naming: `feature/xxx` for features, `fix/xxx` for bugs
- Never force push to `main`
