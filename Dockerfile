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

# Copy built frontend
COPY --from=frontend-build /app/frontend/build /app/frontend/build

WORKDIR /app/backend

# Create cache and data directories
RUN mkdir -p /app/backend/.cache/composer_images /data

# OpenShift / RHEL SCC compatibility:
#   - Primary group set to GID 0 (root group) so the arbitrary UID assigned by
#     OpenShift namespace ranges is always in a group that owns the files.
#   - chmod g=u mirrors user permissions onto the group so any UID in group 0
#     can read and write the same paths as UID 1000.
#   - Numeric USER is required; named users are not resolvable in OpenShift.
RUN useradd -m -u 1000 -g 0 -s /bin/bash maestro \
    && chown -R 1000:0 /app /data \
    && chmod -R g=u /app /data
USER 1000

# Default env vars
ENV MAESTRO_DATASET_PATH=/data
ENV MAESTRO_IMAGE_CACHE_DIR=/app/backend/.cache/composer_images
ENV MAESTRO_HOST=0.0.0.0
ENV MAESTRO_PORT=8000
# Set MAESTRO_UID and MAESTRO_GID to match ownership of mounted dataset volume
# ENV MAESTRO_UID=1000
# ENV MAESTRO_GID=1000

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
