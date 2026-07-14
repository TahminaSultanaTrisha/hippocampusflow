# Deploying HippocampusFlow

## Architecture in production
- Backend: Railway (Docker) + Railway Postgres + Railway Volume for images
- App: run locally pointing at the cloud URL, or host the web build on Netlify

## Backend on Railway
1. Push this repo to GitHub (private repo is fine).
2. railway.app -> New Project -> Deploy from GitHub repo -> pick the repo.
3. In the service Settings -> set **Root Directory** to `backend`
   (Railway then builds using backend/Dockerfile).
4. Add a **Postgres** database to the project (right-click canvas -> Database
   -> PostgreSQL). In the backend service -> Variables -> add a variable
   reference: DATABASE_URL -> ${{Postgres.DATABASE_URL}}.
5. Add a **Volume** to the backend service, mount path: `/data`.
6. Set these Variables on the backend service:
   - JWT_SECRET = a long random string (50+ chars)
   - ANTHROPIC_API_KEY = your key
   - UPLOAD_DIR = /data/uploads
   - FREE_SCAN_LIMIT = 10
7. Settings -> Networking -> Generate Domain. You get
   https://<something>.up.railway.app
8. Open https://<domain>/docs -- if the API console loads, you are live.
   (Migrations run automatically on each deploy via the Dockerfile CMD.)

## Point the app at production
flutter run -d chrome --web-port=5000 --dart-define=API_BASE_URL=https://<your-domain>.up.railway.app

## Optional: host the web app (use it from your phone)
1. flutter build web --dart-define=API_BASE_URL=https://<your-domain>.up.railway.app
2. app/build/web now contains a static site.
3. netlify.com -> drag-and-drop the build/web folder onto the deploy area.
4. Open the Netlify URL on your phone. HTTPS is automatic, so the camera works.

## Notes
- Every git push to main redeploys the backend automatically.
- Images live on the Railway volume; scale-up path is Cloudflare R2 later
  (swap the internals of storage_service.py).
- Tighten CORS in app/main.py to your Netlify domain before a public launch.
