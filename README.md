# Orderly App — CI/CD Pipeline Portfolio Project

A FastAPI application demonstrating a production-grade CI/CD pipeline with:
- **GitHub Actions** for CI (test, build, scan, push)
- **Docker** multi-stage builds
- **Trivy** vulnerability scanning
- **AWS ECR** for container image storage
- **GitOps** deployment via ArgoCD

## Architecture
Code Push → GitHub Actions → Test → Build → Scan → Push to ECR → Update GitOps Repo → ArgoCD → Kubernetes

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Application info |
| `GET /health` | Liveness probe |
| `GET /ready` | Readiness probe |
| `GET /info` | Pod/host information |

## Tech Stack

- Python 3 + FastAPI
- Docker (multi-stage build)
- GitHub Actions
- AWS ECR
- Trivy
- Kubernetes + Helm + ArgoCD

## Related Repository

- GitOps Config: [orderly-app-gitops](https://github.com/rahmansabiurfx/orderly-app-gitops)
