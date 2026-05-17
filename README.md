# orderly-app

A production-style CI/CD pipeline project built with FastAPI, Docker, GitHub Actions, AWS ECR, Kubernetes, Helm, and ArgoCD — deployed across isolated dev, staging, and production environments using GitOps.

> **GitOps config repo:** [orderly-app-gitops](https://github.com/rahmansabiurfx/orderly-app-gitops)

---

## Pipeline Overview

```
git push
   │
   ▼
GitHub Actions
   ├── Lint (flake8)
   ├── Test (pytest)
   ├── Build (Docker multi-stage)
   ├── Scan (Trivy — blocks on CRITICAL CVEs)
   ├── Push to AWS ECR (tagged with git SHA)
   └── Update image.tag in orderly-app-gitops
          │
          ▼
       ArgoCD (watches gitops repo)
          ├── orderly-app-dev     → namespace: dev
          ├── orderly-app-staging → namespace: staging
          └── orderly-app-prod    → namespace: prod
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Application | Python 3.13 + FastAPI |
| Containerisation | Docker (multi-stage build, non-root user) |
| CI | GitHub Actions |
| Image Registry | AWS ECR |
| Security Scanning | Trivy |
| Orchestration | Kubernetes (Kind for local) |
| Packaging | Helm |
| CD / GitOps | ArgoCD |

---

## Application Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Application info and version |
| `/health` | GET | Liveness probe (used by Kubernetes) |
| `/ready` | GET | Readiness probe (used by Kubernetes) |
| `/info` | GET | Pod name, host, environment |

---

## Project Structure

```
orderly-app/
├── .github/
│   └── workflows/
│       └── ci.yaml                   # Full CI pipeline
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI application
│   ├── requirements.txt
│   └── tests/
│       ├── __init__.py
│       └── test_main.py              # pytest test suite
├── infrastructure/
│   └── ecr/
│       ├── main.tf
│       ├── outputs.tf
│       └── provider.tf
├── k8s-local/
│   └── kind-config.yaml
├── .dockerignore
├── .gitignore
├── docker-compose.yaml
├── Dockerfile                        # Multi-stage, non-root
└── README.md
```

---

## CI Pipeline Stages

### 1 — Lint
Runs `flake8` to enforce code style. Fails fast before wasting time on a build.

### 2 — Test
Runs `pytest` with the FastAPI `TestClient`. All endpoints are covered. Pipeline fails if any test fails.

### 3 — Build
Multi-stage Docker build:
- **Stage 1 (builder):** Installs dependencies into a virtual environment
- **Stage 2 (runtime):** Copies only the venv and app code — no build tools in the final image
- Runs as a non-root user (`appuser`) for security

### 4 — Scan
Trivy scans the built image for known CVEs. The pipeline is configured to **block on CRITICAL severity** vulnerabilities and exit with a non-zero code if any are found.

### 5 — Push
On a successful scan, the image is pushed to AWS ECR tagged with the git commit SHA (`abc123f`). Never uses `latest` — every image is uniquely identifiable.

### 6 — Update GitOps
The pipeline opens a commit in `orderly-app-gitops` updating `helm-chart/values.yaml` → `image.tag` to the new SHA. ArgoCD picks this up and deploys within 3 minutes.

---

## Environments

Three isolated Kubernetes namespaces, each managed by a separate ArgoCD Application:

| Environment | Namespace | Replicas | Autoscaling | Ingress Host |
|---|---|---|---|---|
| Dev | `dev` | 2 | Disabled | `orderly-app.dev.local` |
| Staging | `staging` | 2 | Enabled (max 4) | `orderly-app.staging.local` |
| Prod | `prod` | 3 | Enabled (max 6) | `orderly-app.prod.local` |

---

## Key Design Decisions

**Two-repo pattern:** Application code and deployment configuration live in separate repositories. This means a Dockerfile change doesn't affect the gitops history, and a values file change doesn't trigger a new image build.

**Image tagging with git SHA:** Every image is tagged with the exact commit that produced it. No `latest` tag. If something breaks in prod, you can trace the exact code that caused it.

**Non-root container:** The Dockerfile creates a dedicated `appuser` and switches to it before the entrypoint. Kubernetes also enforces `runAsNonRoot: true` at the pod level as a second layer.

**Self-healing via ArgoCD:** All three ArgoCD Applications have `selfHeal: true`. If someone manually changes a resource in the cluster (wrong replica count, deleted ConfigMap, modified env var), ArgoCD reverts it to match Git within the polling interval.

**Separate probes:** `/health` is the liveness probe — Kubernetes restarts the pod if it fails. `/ready` is the readiness probe — Kubernetes removes the pod from the Service (stops sending traffic) but does not restart it. These serve different purposes and are not interchangeable.