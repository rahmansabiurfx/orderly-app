# ════════════════════════════════════════════════════════════════
# STAGE 1: Builder
# Purpose: Install ALL dependencies, run tests
# ════════════════════════════════════════════════════════════════

FROM python:3.13-slim AS builder
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY app/ ./app/
RUN python3 -m pytest app/tests/ -v --tb=short

# ════════════════════════════════════════════════════════════════
# STAGE 2: Production
# Purpose: Minimal image with ONLY what's needed to run the app
# ════════════════════════════════════════════════════════════════
FROM python:3.13-slim AS production
LABEL maintainer="Orderly Portfolio Project"
LABEL desscription="FastAPI application for CI/CD pipeline demonstration"
RUN useradd -r -s /bin/false appuser
WORKDIR /app
COPY --from=builder /root/.local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /root/.local/bin /usr/local/bin
COPY --from=builder /app/app ./app/
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=30s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2", "--no-access-log"]