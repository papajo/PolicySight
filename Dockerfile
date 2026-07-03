# Backend
FROM python:3.11-slim AS backend

WORKDIR /app/backend

COPY backend/pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Frontend build stage
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Nginx for serving frontend
FROM nginx:alpine AS frontend

COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80