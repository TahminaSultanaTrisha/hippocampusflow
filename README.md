# HippocampusFlow — Phase 0

Camera-first AI assistant. This is the Phase 0 foundation: working auth,
database migrations, tested backend, and a Flutter app shell with an
auth-aware router.

## Repository layout

```
backend/   FastAPI + SQLAlchemy + Alembic (Python 3.12)
app/       Flutter app (iOS + Android)
.github/   CI: backend tests run on every push and PR
```

## Run the backend (zero setup — uses SQLite by default)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # edit JWT_SECRET before deploying anywhere
alembic upgrade head          # creates the database schema
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs — FastAPI gives you a free interactive API
console. Try POST /auth/register there.

Run the tests any time: `pytest -q` (5 tests cover the Phase 0 exit criteria).

Switch to Postgres later by changing one line in `.env`:
`DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/hippocampusflow`

## Run the Flutter app

Prereqs: Flutter SDK installed (`flutter doctor` all green), and the backend
running.

```bash
cd app
flutter create . --platforms=ios,android   # generates ios/ + android/ folders
flutter pub get
flutter run
```

Note: `flutter create .` only generates the native platform folders — it will
not overwrite lib/ or pubspec.yaml. Run it once after cloning.

API address: the app defaults to `http://10.0.2.2:8000` (how the **Android
emulator** reaches your machine's localhost). For the **iOS simulator**:

```bash
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

For a **real phone**, use your computer's LAN IP, e.g.
`--dart-define=API_BASE_URL=http://192.168.1.20:8000`.

## What works right now (Phase 0 exit criteria)

- Create an account and sign in from the app
- Tokens stored in encrypted device storage; sessions survive app restarts
- Expired access tokens refresh silently (Dio interceptor)
- Protected endpoint `/users/me` returns your profile
- `pytest` proves register / login / refresh / protection / duplicate-email
- CI runs the test suite on every push

## Next: Phase 1

Camera capture → image upload → object storage → scan history list.
