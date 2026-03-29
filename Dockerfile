# Stage 1: Build frontend
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + serve frontend
FROM python:3.13-slim AS production

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install Python dependencies
COPY backend/pyproject.toml backend/uv.lock* ./backend/
WORKDIR /app/backend
RUN uv sync --frozen --no-dev

# Copy backend source
COPY backend/ ./

# Dataset is relatively small, copy it to the image for simplicity for now
COPY MaestroDataset/ /data/

# Copy built frontend
COPY --from=frontend-build /app/frontend/build /app/frontend/build

WORKDIR /app/backend

# Create cache directory for composer images
RUN mkdir -p /app/backend/.cache/composer_images

# Default env vars
ENV MAESTRO_DATASET_PATH=/data
ENV MAESTRO_IMAGE_CACHE_DIR=/app/backend/.cache/composer_images
ENV MAESTRO_HOST=0.0.0.0
ENV MAESTRO_PORT=8000

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
