# HippocampusFlow 🧠📷

Camera-first AI assistant: point your camera at anything and get
identification, explanation, actions, and memory.

**Scan → AI understands → Structured result + actions → Ask follow-ups → It remembers.**

## Features
- 18 specialist AI agents (receipt, product, food, cooking, plant, animal,
  vehicle, fashion, repair, travel, and more) routed automatically by a
  vision classifier
- Real actions: expense tracking from receipts, meal logging with calorie
  tallies, wishlists
- Personal memory: every scan becomes a memory; ask "what was that mug I
  scanned?" and get an answer from your own history
- Per-scan AI chat with image context
- Privacy controls: full-erasure scan delete (single and bulk), manage and
  forget individual memories, ID-document extraction guardrails
- Free tier (10 scans/month) with premium tier skeleton
- Onboarding, auth with silent token refresh, scan history with search

## Stack
- **Backend:** FastAPI · SQLAlchemy · Alembic · Postgres (SQLite in dev) · Anthropic API (Haiku classifier + Sonnet agents)
- **App:** Flutter (web/Android/iOS) · Riverpod · go_router · Dio
- **Tests:** 27 backend tests (pytest), CI via GitHub Actions

## Repository layout
- `backend/` — FastAPI API + AI pipeline + tests
- `app/` — Flutter app
- `DEPLOYMENT.md` — Railway + Netlify deployment guide

## Run locally

Backend (needs an `ANTHROPIC_API_KEY` in `backend/.env`, see `.env.example`):

    cd backend
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env
    alembic upgrade head
    uvicorn app.main:app --reload --reload-dir app

App:

    cd app
    flutter create . --platforms=android
    flutter pub get
    flutter run -d chrome --web-port=5000 --dart-define=API_BASE_URL=http://localhost:8000

## Deploy
See [DEPLOYMENT.md](DEPLOYMENT.md) — Railway (backend + Postgres + volume) and Netlify (web app).
