# ===== Backend =====
FROM python:3.11-slim AS backend-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY backend/src ./src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ===== Frontend Build =====
FROM node:20-alpine AS frontend-build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit

COPY frontend/ .
RUN npm run build

# ===== Nginx (serves frontend + proxies API) =====
FROM nginx:alpine

COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1