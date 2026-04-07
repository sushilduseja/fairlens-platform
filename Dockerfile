# syntax=docker/dockerfile:1

FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend ./backend
COPY alembic.ini ./alembic.ini
COPY sample-data ./sample-data
COPY pyproject.toml ./pyproject.toml

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY --from=frontend-build /app/frontend/dist ./backend/static

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
