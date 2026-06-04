# AWS Deployment Readiness Plan

BackPocket OS AI is not ready for production deployment yet. This document defines the safe path from the current local/mini-PC oriented system to an AWS deployment.

## Decision Record

Preferred target: ECS Fargate + Application Load Balancer for the backend, S3 + CloudFront for Flutter web, RDS PostgreSQL for durable application data, and AWS Secrets Manager for runtime secrets.

ECS Fargate is preferred over App Runner for this repo because BackPocket OS currently has multiple operational concerns that need separation and control:

- FastAPI web traffic.
- Background Gmail polling.
- Local OAuth token files.
- SQLite-first modules.
- Future Paperless services.
- Potential persistent volumes during migration.

App Runner remains a possible prototype option for a simple single-container web service, but it is less aligned with the current need to split web and worker tasks, control storage, and run related services. Elastic Beanstalk is also viable, but ECS maps more cleanly to the intended production architecture.

## Target Architecture

Production target:

- Flutter web: S3 static hosting behind CloudFront and ACM TLS.
- API: ECS Fargate service behind an Application Load Balancer.
- Database: RDS PostgreSQL, private subnet, automated backups enabled.
- Secrets: AWS Secrets Manager injected into ECS task definitions.
- Files/uploads: S3 for durable uploaded objects; EFS only as a temporary bridge if needed.
- Worker: separate ECS service or scheduled ECS task for Gmail polling and background jobs.
- Logs/metrics: CloudWatch Logs, CloudWatch alarms, ALB health checks.

Temporary bridge option:

- Single ECS task with EFS-backed SQLite for the first AWS smoke deployment.
- This is only acceptable for a short-lived MVP validation because SQLite plus EFS is not the production data target and does not solve horizontal scaling.
- Run only one web task while using this bridge, and keep backups explicit.

## Not Ready For Production Caveats

- Many modules still connect directly to SQLite and `backpocket.db`.
- Background Gmail polling currently starts inside the FastAPI web process.
- Gmail OAuth tokens are local files and need managed storage.
- Paperless deployment is not included in Phase 1.
- Docker image still needs production hardening.
- The worktree has many unrelated dirty changes and needs grouped commits before push.

## Phase 0: Pre-Push Cleanup

- Group changes into coherent commits before push:
  - backend auth/tests
  - Docker/pre-push safety
  - Flutter runtime fixes
  - MCP/backend feature changes
  - docs/deployment planning
- Confirm `.env`, OAuth tokens, SQLite DBs, uploads, and generated build artifacts are not tracked.
- Keep `.dockerignore` in place before any ECR build.
- Verify:
  - `pytest -q`
  - `python3 -c "import main"`
  - `dart analyze` when Flutter changes
  - `flutter build web --release --dart-define=BP_API_KEY=` when Flutter changes
  - `docker build -t backpocket-os-ai:audit .`
- Confirm production startup fails if neither `BP_API_KEY` nor `SUPABASE_JWT_SECRET` is configured.

## Phase 1: Minimal AWS MVP

Goal: prove the app can run on AWS without making irreversible architecture commitments.

- Build and push backend image to ECR.
- Deploy one ECS Fargate API task behind an ALB.
- Use `/health` or `/api/health` for ALB health checks.
- Configure `FRONTEND_ORIGIN` for the deployed CloudFront or app domain.
- Store `BP_API_KEY`, Gemini/OpenRouter keys, webhook secrets, and other sensitive values in Secrets Manager.
- Build Flutter web and publish it to S3 + CloudFront.
- Use a single API task if SQLite/EFS bridge is used.
- Do not deploy Paperless in this phase.

Exit criteria:

- API health checks pass through ALB.
- Flutter web can call the API through the deployed origin.
- Auth is required for protected endpoints.
- Logs are visible in CloudWatch.
- No secrets are present in image layers or repository history.

## Phase 2: Data Migration

Goal: move from SQLite-first local persistence to production-grade RDS PostgreSQL.

- Inventory all direct `sqlite3.connect`, `DB_PATH`, and `backpocket.db` call sites.
- Replace direct SQLite access with a shared DB abstraction or SQLAlchemy layer.
- Add migration tests that run against SQLite and PostgreSQL-compatible behavior where practical.
- Run SQLite-to-Postgres migration in a staging environment.
- Enable RDS automated backups and define restore drills.
- Only scale ECS API task count above one after the database migration is complete.

Do not perform this migration as part of the current pre-push readiness work.

## Phase 3: Worker Split

Goal: prevent every web replica from polling Gmail or running duplicate background work.

- Disable web-process polling in ECS web tasks.
- Move Gmail polling to:
  - a separate ECS worker service, or
  - an EventBridge scheduled ECS task.
- Add singleton/locking behavior for any job that must not run concurrently.
- Move worker logs into CloudWatch with alarms for failures.

Do not split the worker as part of the current pre-push readiness work.

## Phase 4: Hardening

- Run the Docker image as a non-root user.
- Move build tools out of the final image with a multi-stage build.
- Add CloudWatch alarms for 5xx, failed health checks, task restarts, and worker failures.
- Add WAF if the API is exposed publicly.
- Add Route 53 and ACM-managed HTTPS.
- Define backup and restore playbooks.
- Add CI/CD for:
  - tests
  - Flutter build
  - Docker build
  - ECR push
  - ECS deployment
- Add staging before production.

## Paperless Deferral

Paperless is Phase 2 or later. It should be deployed as its own service stack with its own database, Redis, storage, secrets, backups, and operational checks. Do not include Paperless in the first AWS MVP.
