# orderly-app

A production-style CI/CD pipeline project built with FastAPI, Docker, GitHub Actions, AWS ECR, Helm, and ArgoCD — running locally on a Kind Kubernetes cluster across isolated dev, staging, and production environments using GitOps with staged promotion and manual approval gates. Kind was chosen to provide a fully reproducible local Kubernetes environment without requiring managed cloud infrastructure.

> **GitOps config repo:** [orderly-app-gitops](https://github.com/rahmansabiurfx/orderly-app-gitops)

---

## Architecture

```
Developer Push
      │
      ▼
┌──────────────────────────────────────────────────┐
│              GitHub Actions (CI/CD)              │
│                                                  │
│  Lint → Test → Build → Scan → Push to ECR        │
│                    │                             │
│         ┌──────────┼──────────┐                  │
│         ▼          ▼          ▼                  │
│    Auto (dev)  Approval   Approval               │
│                (staging)   (prod)                │
└─────┬──────────────┬──────────┬──────────────────┘
      │              │          │
      ▼              ▼          ▼
values-dev.yaml  values-staging.yaml  values-prod.yaml
      │              │          │
      └──────────────┴──────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │      ArgoCD           │
         │  (watches gitops repo)│
         └───────────┬───────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │  Kind Kubernetes       │
         │  ├── namespace: dev    │
         │  ├── namespace: staging│
         │  └── namespace: prod   │
         └────────────────────────┘
```

---

## Pipeline Overview

```
git push
   │
   ▼
GitHub Actions
   ├── Lint + Format check (Ruff)
   ├── Test (pytest)
   ├── Build (Docker multi-stage)
   ├── Scan (Trivy — blocks on CRITICAL + HIGH CVEs)
   ├── Push to AWS ECR (tagged with git SHA)
   │
   ├── Deploy → Dev      (automatic)
   │     └── updates values-dev.yaml → ArgoCD syncs dev namespace
   │
   ├── Deploy → Staging  (manual approval required)
   │     └── updates values-staging.yaml → ArgoCD syncs staging namespace
   │
   └── Deploy → Prod     (manual approval required)
         └── updates values-prod.yaml → ArgoCD syncs prod namespace
```

Each stage is gated — staging will not deploy if dev fails, prod will not deploy until staging is approved. If a bug is found in dev or staging, the pipeline stops there and prod is never touched.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Application | Python 3.13.5 + FastAPI |
| Containerisation | Docker (multi-stage build, non-root user) |
| Linting + Formatting | Ruff |
| Testing | pytest |
| CI | GitHub Actions |
| Image Registry | AWS ECR |
| Security Scanning | Trivy |
| Orchestration | Kubernetes (Kind — local cluster) |
| Packaging | Helm |
| CD / GitOps | ArgoCD |
| Autoscaling | Kubernetes HPA + metrics-server |

---

## Security Features

- **Non-root containers** — runs as UID 65534 (nobody); no root access inside the pod
- **Immutable image tags** — every image is tagged with its git commit SHA; `latest` is never used
- **Trivy image scanning** — scans every image before it is pushed to ECR; blocks on CRITICAL and HIGH CVEs with available fixes
- **OS package upgrades at build time** — `apt-get upgrade` runs in the production stage to reduce base image CVE exposure
- **Approval gates** — staging and prod require explicit human sign-off before the pipeline writes a new image tag to their GitOps manifests
- **GitOps reconciliation** — ArgoCD enforces cluster state from Git; manual `kubectl` changes are automatically reverted
- **No manual deployments** — the only path to any environment is through Git and the pipeline

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
│       └── ci.yaml                   # Full CI/CD pipeline with approval gates
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI application
│   ├── requirements.txt              # App + dev dependencies (pytest, ruff)
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
├── Dockerfile                        # Multi-stage, non-root, OS-patched
└── README.md
```

---

## CI/CD Pipeline Stages

### 1 — Lint + Format Check
Ruff runs two checks in one step:
- `ruff check` — catches code errors and style violations (replaces flake8)
- `ruff format --check` — verifies formatting without modifying files (replaces black)

Pipeline fails immediately if either check fails, before wasting time on a build.

### 2 — Test
Runs `pytest` with the FastAPI `TestClient`. All four endpoints are covered. Pipeline fails if any test fails.

### 3 — Build
Multi-stage Docker build:
- **Stage 1 (builder):** Installs dependencies, runs tests as a build-time gate
- **Stage 2 (production):** Runs `apt-get upgrade` to reduce known OS-level vulnerabilities at build time, then copies only the app code and installed packages — no build tools in the final image
- Runs as UID `65534` (nobody) — non-root by default

### 4 — Scan
Trivy scans the built image for known CVEs. Configured to block on **CRITICAL and HIGH** severity with `ignore-unfixed: true` so only vulnerabilities with available patches are flagged. This reduces noise from transitive OS library CVEs that are not yet patchable, while still catching actionable issues.

### 5 — Push
On a successful scan, the image is pushed to AWS ECR tagged with the 7-character git commit SHA (e.g. `2b07101`). Never uses `latest` — every image is uniquely traceable to the exact commit that produced it.

### 6 — Deploy to Dev (automatic)
Updates `image.tag` in `helm-chart/values-dev.yaml` in the gitops repo. ArgoCD detects the change and performs a rolling update in the `dev` namespace automatically.

### 7 — Deploy to Staging (manual approval)
Pauses and waits for a reviewer to approve in GitHub Actions. Only updates `helm-chart/values-staging.yaml` — staging runs on whatever tag it had before until approved. If the dev deployment revealed a bug, the reviewer rejects and prod is never touched.

### 8 — Deploy to Prod (manual approval)
Second approval gate. Only updates `helm-chart/values-prod.yaml` after explicit sign-off. The pipeline never writes to `values-prod.yaml` until this job runs — prod is gated at the GitOps manifest level, not just the workflow level.

---

## Environments

Three isolated Kubernetes namespaces on a local Kind cluster, each managed by a separate ArgoCD Application with its own image tag:

| Environment | Namespace | Replicas | Autoscaling | Ingress Host | Deployment |
|---|---|---|---|---|---|
| Dev | `dev` | 2 | Disabled | `orderly-app.dev.local` | Automatic |
| Staging | `staging` | 2–4 | Enabled (HPA) | `orderly-app.staging.local` | Manual approval |
| Prod | `prod` | 3–6 | Enabled (HPA) | `orderly-app.prod.local` | Manual approval |

---

## Key Design Decisions

**Two-repo pattern:** Application code and deployment configuration live in separate repositories. A Dockerfile change doesn't pollute the gitops history, and a values file change doesn't trigger a new image build.

**Per-environment image tags:** Each environment has its own `image.tag` in its own values file (`values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml`). The CI pipeline updates them independently per stage. Dev and prod can run different versions simultaneously — prod only moves when explicitly approved.

**Image tagging with git SHA:** Every image is tagged with the exact commit that produced it. No `latest` tag. If something breaks in prod, you can trace the exact code that caused it and roll back to any previous SHA.

**Staged promotion with approval gates:** Dev deploys automatically on every push to main. Staging and prod require a named reviewer to approve in GitHub before the pipeline writes the new tag to their values files. Environment promotion is controlled via independent GitOps manifests per environment — each environment's values file is updated in isolation, not as part of a shared state change.

**OS package upgrades at build time:** The production stage runs `apt-get upgrade -y` during every image build to reduce exposure to known fixed vulnerabilities in base image packages. Long-term CVE remediation also depends on periodically pulling newer base image versions, as some vulnerabilities require a base image rebuild rather than a package upgrade.

**Trivy scanning with actionable alerts:** Trivy is configured with `ignore-unfixed: true` so the pipeline only blocks on CVEs that have an available fix. This avoids alert fatigue from transitive OS library vulnerabilities that are not yet patchable, while still enforcing a hard gate on CRITICAL and HIGH severity issues that can be resolved.

**Self-healing via ArgoCD:** All three ArgoCD Applications are configured with automated sync, pruning, and self-healing enabled. Automated sync applies Git changes to the cluster without manual intervention. Pruning removes resources that are deleted from Git. Self-healing reverts any manual `kubectl` changes back to the Git state within the reconciliation cycle. Git is the only way to make a permanent change.

**Separate probes:** `/health` is the liveness probe — Kubernetes restarts the pod if it fails. `/ready` is the readiness probe — Kubernetes stops sending traffic to the pod but does not restart it. These serve different purposes and are not interchangeable.

**HPA with metrics-server:** Staging and prod use Horizontal Pod Autoscaler scaling on CPU utilisation (target 70%). metrics-server is installed on the Kind cluster with `--kubelet-insecure-tls` to enable HPA on local nodes.

---

## Rollback Strategy

Rollback is handled through Git — the source of truth for all deployments.

**To roll back prod to a previous version:**

```bash
# In orderly-app-gitops
git log helm-chart/values-prod.yaml          # find the previous commit
git revert <commit-sha>                       # revert the tag update
git push origin main                          # ArgoCD detects the change and redeploys
```

ArgoCD detects the reverted `image.tag` in `values-prod.yaml` during its reconciliation cycle and performs a rolling update back to the previous image — no `kubectl` commands needed.

**Next maturity step:** In production teams this is typically extended with an ArgoCD rollback hook or a dedicated "promote previous SHA" pipeline job, so operators can roll back from the ArgoCD UI or a Slack command without touching Git manually.

---

## Future Improvements

- **GitHub OIDC → AWS IAM role assumption** — replace long-lived AWS access keys with short-lived credentials via OIDC federation; no secrets stored in GitHub
- **External Secrets Operator** — pull secrets from AWS Secrets Manager or HashiCorp Vault into Kubernetes at runtime rather than storing them as static Kubernetes Secrets
- **Prometheus + Grafana** — cluster and application observability; alerting on error rates, latency, and pod restarts
- **Progressive delivery with Argo Rollouts** — replace standard rolling updates with canary or blue/green deployments, with automatic rollback on metric degradation