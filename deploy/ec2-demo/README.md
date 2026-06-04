# EC2 Docker Compose Demo

This folder is the safe EC2 live-demo path for BackPocket OS AI. It is intentionally smaller than the root `docker-compose.yml`.

It runs only the FastAPI backend, serves the checked-in static dashboard, persists SQLite as a host-mounted `backpocket.db`, requires `BP_API_KEY`, disables background Gmail polling, and keeps `DEMO_MODE=1` by default.

This is not a production deployment.

## What Runs

- FastAPI backend on container port `8000`.
- SQLite mounted from `./data/backpocket.db` to `/app/backpocket.db`.
- Static dashboard at `/static/index.html`.
- Flutter web at `/app/` only if a `static_flutter/` build is intentionally mounted.

## What Does Not Run

- Paperless.
- MCP servers or OpenCode tooling.
- RDS, ECS, ALB, CloudFront, or any AWS managed production services.
- Real Gmail or WhatsApp sends while `DEMO_MODE=1`.
- Background Gmail polling while `DISABLE_BACKGROUND_POLLING=1`.

## EC2 Steps

From the repo root on the EC2 instance:

```bash
cd deploy/ec2-demo
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(24))"
```

Put the generated value into `.env` as `BP_API_KEY`.

Prepare the host-mounted SQLite file and runtime folders:

```bash
mkdir -p data/uploads data/documents data/logs
touch data/backpocket.db
```

Start the demo stack:

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

Smoke test on the EC2 box:

```bash
set -a
. ./.env
set +a
curl http://127.0.0.1:8000/api/health
curl -I "http://127.0.0.1:8000/static/index.html?api_key=$BP_API_KEY"
curl -i http://127.0.0.1:8000/api/status
curl -i -H "X-API-Key: $BP_API_KEY" http://127.0.0.1:8000/api/status
```

Open the EC2 security group for the chosen `BP_PUBLIC_PORT` only. The default is `8000`.

## Demo URLs

Replace `EC2_PUBLIC_IP` and `YOUR_BP_API_KEY`:

```text
http://EC2_PUBLIC_IP:8000/api/health
http://EC2_PUBLIC_IP:8000/static/index.html?api_key=YOUR_BP_API_KEY
```

Flutter web is not the default demo route because `static_flutter/` is not currently present and is ignored by Docker builds. If you intentionally prepare a Flutter build, uncomment the optional `static_flutter` volume in `docker-compose.yml`, build/copy the Flutter output to `static_flutter/`, then use:

```text
http://EC2_PUBLIC_IP:8000/app/
```

## Safe Defaults

- Optional integration keys use `DEMO_*` variable names so host shell secrets are not injected accidentally.
- `DEMO_MODE=1` blocks Gmail send calls and WhatsApp send calls at the service layer.
- `DISABLE_BACKGROUND_POLLING=1` stops startup Gmail polling and disables `/run-poll`.
- `REQUIRE_BP_API_KEY=1` blocks startup unless `BP_API_KEY` is set to a non-placeholder value.
- Protected `/api/*` endpoints require `X-API-Key: <BP_API_KEY>` or `?api_key=<BP_API_KEY>`.

## Limitations

- Not production-ready.
- SQLite is single-instance only and should not be horizontally scaled.
- Gmail tokens are local/demo-only and are not mounted in this demo stack.
- Background polling should be split into a worker before production.
- Paperless is deferred and not part of this stack.
- MCP tooling is not part of the web demo runtime.
- RDS/Postgres migration is needed for scalable deployment.
- Use the root `AWS_DEPLOYMENT_PLAN.md` for the real production path.

## Shutdown

```bash
docker compose down
```
