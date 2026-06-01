# Build stage
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY pyproject.toml setup.py ./
COPY viabilityscan/ ./viabilityscan/
COPY core/ ./core/
COPY django_project/ ./django_project/
COPY manage.py ./

RUN pip install --no-cache-dir -e ".[django]" gunicorn

# Production stage
FROM python:3.13-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY --from=builder /app .
COPY dashboard/ ./dashboard/
COPY tests/ ./tests/
COPY .github/ ./.github/
COPY Makefile README.md LICENSE SECURITY.md CONTRIBUTING.md ./

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R appuser:appgroup /app

USER appuser

ENV DJANGO_SETTINGS_MODULE=django_project.settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Run migrations and start gunicorn
CMD python manage.py migrate --run-syncdb && \
    gunicorn django_project.wsgi:application --bind 0.0.0.0:8000 --workers 2
