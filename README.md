# FairLens Platform

MVP fairness audit platform.

## Stack
- FastAPI backend
- React + Vite frontend
- SQLite + Redis

## Run (local)
1. Install backend deps in project-local `.venv`.
2. Install frontend deps with local cache: `cmd /c npm --prefix frontend install --cache .npm-cache`.
3. Start backend: `uvicorn backend.main:app --reload --port 8000`.
4. Start frontend: `cmd /c npm --prefix frontend run dev`.

## Docker
`docker compose up --build`

## Authentication

The app implements JWT-based authentication with API keys.

### Auth Flow for Hiring Managers
1. **Visit app** → Redirected to `/login` (or `/register` for new users)
2. **Register** → Create account → Get API key displayed → "Go to Dashboard"
3. **Login** → Enter credentials → Redirected to Dashboard
4. **Protected routes** → Any `/` (Dashboard), `/audits/new`, `/metrics` redirects to login if not authenticated
5. **Logout** → Click "Sign out" in sidebar → Clears token → Redirected to login

### API Endpoints
- `POST /api/v1/auth/register` - Create account, returns `user_id`, `api_key`
- `POST /api/v1/auth/login` - Login, returns `session_token`, `user`
- `GET /api/v1/auth/me` - Get current user (requires auth)
- `GET /api/v1/healthz` - Public health check

### Auth Tests
```bash
# Backend
python -m pytest backend/tests/test_auth.py -v

# Frontend
cd frontend && npm run test:run
```
