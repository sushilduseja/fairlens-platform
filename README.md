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
