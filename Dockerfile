# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1 — build the React/Vite frontend into static assets
# ---------------------------------------------------------------------------
FROM node:20-slim AS frontend
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2 — Python backend that also serves the built frontend
# ---------------------------------------------------------------------------
FROM python:3.11-slim
WORKDIR /app/backend

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# main.py mounts ../frontend/dist relative to itself, i.e. /app/frontend/dist
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Cloud hosts (Render/Railway/Fly) inject the port via $PORT; default to 8000 locally.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
