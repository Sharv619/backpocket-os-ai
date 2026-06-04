# Production Checklist

Use this checklist before any AWS production deployment. BackPocket OS AI is not production-ready until every required item is addressed or explicitly accepted as a temporary risk.

## Auth And Secrets

- [ ] `ENV`, `APP_ENV`, or `NODE_ENV` is set to `production`.
- [ ] At least one real production auth secret is configured:
  - `BP_API_KEY`, or
  - `SUPABASE_JWT_SECRET`
- [ ] Placeholder values are not accepted as production auth secrets.
- [ ] Secrets are stored in AWS Secrets Manager, not repository files or Docker image layers.
- [ ] `.env` is not committed.
- [ ] OAuth token files are not committed or copied into images.

## CORS

- [ ] `FRONTEND_ORIGIN` is set to the deployed CloudFront/app origin.
- [ ] Localhost/LAN origins are acceptable only for dev/staging.
- [ ] Browser `OPTIONS` preflight requests return successfully.

## Database

- [ ] Current SQLite-first implementation is accepted only for local or temporary single-task AWS bridge.
- [ ] Production target is RDS PostgreSQL.
- [ ] Direct SQLite call sites are migrated or wrapped before horizontal scaling.
- [ ] Migration plan and rollback plan are written.

## Worker Separation

- [ ] Gmail polling does not run in every API web replica.
- [ ] Background jobs are moved to a worker service or scheduled ECS task.
- [ ] Duplicate job prevention is implemented for non-idempotent jobs.

## Gmail Token Storage

- [ ] Gmail OAuth tokens are stored outside the image.
- [ ] Token storage strategy is defined: Secrets Manager, S3 with KMS, or EFS bridge.
- [ ] Token rotation and revocation process is documented.

## Docker Hardening

- [ ] `.dockerignore` excludes secrets, DBs, uploads, logs, and generated artifacts.
- [ ] Container image runs as non-root.
- [ ] Final image does not retain unnecessary build tools.
- [ ] Image is scanned before release.

## Logging And Monitoring

- [ ] ECS task logs go to CloudWatch.
- [ ] Alarms exist for 5xx responses, failed health checks, task restarts, and worker failures.
- [ ] Sensitive values are not logged.

## Health Checks

- [ ] ALB health check uses `/health` or `/api/health`.
- [ ] Health response is unauthenticated.
- [ ] Health response does not expose sensitive config.
- [ ] Expected response is simple JSON: `{ "status": "ok" }`.

## Backup And Restore

- [ ] RDS automated backups are enabled once migrated.
- [ ] SQLite bridge, if used, has explicit backup automation.
- [ ] Restore drill is documented and tested.
- [ ] Upload/object storage backup policy is defined.

## CI/CD

- [ ] CI runs `pytest -q`.
- [ ] CI runs `python3 -c "import main"`.
- [ ] CI runs `dart analyze` when Flutter changes.
- [ ] CI runs Flutter web release build when Flutter changes.
- [ ] CI builds Docker image.
- [ ] Deployment requires staging validation before production.

## Domain And HTTPS

- [ ] Route 53 domain or DNS record is configured.
- [ ] ACM certificate is issued.
- [ ] CloudFront and ALB use HTTPS.
- [ ] HTTP redirects to HTTPS.

## Paperless Deferral

- [ ] Paperless is not included in Phase 1.
- [ ] Paperless deployment plan includes separate storage, database, Redis, secrets, backups, and monitoring.
