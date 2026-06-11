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

# git: repo cloning for scans · curl: health probes · envoy: front proxy / load balancer
RUN apt-get update && apt-get install -y --no-install-recommends git curl gnupg ca-certificates \
    && curl -fsSL https://apt.envoyproxy.io/signing.key | gpg --dearmor -o /usr/share/keyrings/envoy-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/envoy-keyring.gpg] https://apt.envoyproxy.io bookworm main" > /etc/apt/sources.list.d/envoy.list \
    && apt-get update && apt-get install -y --no-install-recommends envoy \
    && apt-get purge -y gnupg && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY --from=builder /app .
COPY templates/ ./templates/
COPY dashboard/ ./dashboard/
COPY tests/ ./tests/
COPY .github/ ./.github/
COPY Makefile README.md LICENSE SECURITY.md CONTRIBUTING.md ./
COPY envoy.yaml start-envoy.sh ./
RUN sed -i 's/\r$//' start-envoy.sh && chmod +x start-envoy.sh

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R appuser:appgroup /app

USER appuser

ENV DJANGO_SETTINGS_MODULE=django_project.settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Envoy front proxy on 8080 → gunicorn upstream on 8081
EXPOSE 8080

CMD ["./start-envoy.sh"]
