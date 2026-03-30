"""
Orderly App - FastAPI Application
Portfolio Project: CI/CD Pipeline with GitOps
"""

import os
import socket
from datetime import datetime, timezone
from fastapi import FastAPI
from contextlib import asynccontextmanager

# ──────────────────────────────────────────────
# Application Configuration
# ──────────────────────────────────────────────

# ──────────────────────────────────────────────
# Lifespan
# ──────────────────────────────────────────────

APP_NAME = os.getenv("APP_NAME", "orderly-app")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{'='*50}")
    print(f"  {APP_NAME} v{APP_VERSION}")
    print(f"  Environment: {ENVIRONMENT}")
    print(f"  Hostname: {socket.gethostname()}")
    print(f"{'='*50}")
    yield

# ──────────────────────────────────────────────
# Creating FastAPI Application Instance
# ──────────────────────────────────────────────

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="DevOps Portfolio Project - CI/CD Pipeline with GitOps Deployment",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────
# Route: GET /
# Purpose: Basic application information
# ──────────────────────────────────────────────

@app.get("/")
def root():
    """
    Returns basic application information.
    Useful for quick verification if the app is running
    and to identify version/env.
    """
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Welcome to the Orderly App!",
    }

# ──────────────────────────────────────────────
# Route: GET /health
# Purpose: Liveness probe for Kubernetes
# ──────────────────────────────────────────────

@app.get("/health")
def health():
    """
    Liveness probe endpoint.
    """
    return{
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ──────────────────────────────────────────────
# Route: GET /ready
# Purpose: Readiness probe for Kubernetes
# ──────────────────────────────────────────────

@app.get("/ready")
def ready():
    """
    Readiness probe endpoint.
    """
    return{
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────
# Route: GET /info
# Purpose: Show which pod/host is responding
# ──────────────────────────────────────────────

@app.get("/info")
def info():
    """
    Returns hostname and runtime info.
    """
    return{
        "hostname": socket.gethostname(),
        "platform": os.name,
        "python_version": os.sys.version,
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "environment": ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
