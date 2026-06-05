# EC2 Docker Compose Demo

This folder is the safe EC2 live-demo path for BackPocket OS AI. It is intentionally smaller than the root `docker-compose.yml`.

It runs only the FastAPI backend, serves the checked-in static dashboard, persists SQLite as a host-mounted `backpocket.db`, requires `BP_API_KEY`, disables background Gmail polling, and keeps `DEMO_MODE=1` by default.

It can also run an optional Caddy edge proxy for HTTPS at `backpocket.himanshulade.com`, but use the existing EC2 reverse proxy if another project already owns ports `80` and `443`.

The recommended demo workflow is still: run the backend on EC2, then run the Flutter app separately and point its server URL to `https://backpocket.himanshulade.com` with the demo `BP_API_KEY`.

This is not a production deployment.

## What Runs

- FastAPI backend on container port `8000`, bound to host `127.0.0.1:8000` by default.
- Optional Caddy reverse proxy on ports `80` and `443` for the demo subdomain. It only starts with `--profile edge`.
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

For the subdomain demo, also set:

```bash
DEMO_DOMAIN=backpocket.himanshulade.com
FRONTEND_ORIGIN=https://backpocket.himanshulade.com
```

Prepare the host-mounted SQLite file and runtime folders:

```bash
mkdir -p data/uploads data/documents data/logs
touch data/backpocket.db
```

Start the demo stack:

```bash
docker compose config
docker compose build
docker compose up -d api
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

Open the EC2 security group for ports `80` and `443`. Port `8000` binds to `127.0.0.1` by default for host-only smoke tests and does not need a public inbound rule.

If you intentionally need direct public `:8000` access for a short test, set `BP_BIND_ADDRESS=0.0.0.0`, restart the stack, and remove that exposure afterwards.

## Existing EC2 Reverse Proxy

If another Docker stack already owns ports `80` and `443`, do not start this stack's Caddy profile. Keep BackPocket running as API-only:

```bash
docker compose up -d api
```

Your EC2 currently has an existing Caddy container named `ec2-caddy-1`. Connect it to the BackPocket Docker network so it can reach the API container directly:

```bash
docker network connect backpocket-os-ai-ec2-demo_default ec2-caddy-1 || true
docker exec ec2-caddy-1 wget -qO- http://backpocket-os-ai-ec2-demo-api-1:8000/api/health
```

Add the site block from `deploy/ec2-demo/caddy-site.backpocket.Caddyfile` to the existing Caddy config, then reload existing Caddy:

```bash
docker exec ec2-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

To find the host-mounted Caddyfile path for the existing Caddy container:

```bash
docker inspect ec2-caddy-1 --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

If the existing proxy is host nginx instead, use `deploy/ec2-demo/nginx-site.backpocket.conf` and proxy to `http://127.0.0.1:8000`.

## Flutter App Separate From Docker

If you run Flutter the usual way, Docker only needs to run the backend and Caddy on EC2.

From your Flutter dev machine:

```bash
cd flutter_prototype/backpocket_mobile
flutter pub get
flutter run -d chrome
```

In the Flutter Settings screen, use:

```text
Server URL: https://backpocket.himanshulade.com
API key: the BP_API_KEY from deploy/ec2-demo/.env on EC2
```

For a release web build instead of `flutter run`, build it separately and serve it from your preferred static host. The API server remains `https://backpocket.himanshulade.com`.

## DNS And HTTPS

Create this DNS record wherever `himanshulade.com` is managed:

```text
Type: A
Name: backpocket
Value: EC2_PUBLIC_IP
TTL: 300
```

If using Cloudflare, use DNS-only mode until Caddy obtains the first certificate. After HTTPS works, proxying can be enabled if desired.

Caddy automatically requests and renews the HTTPS certificate. Ports `80` and `443` must be reachable from the internet for certificate issuance.

If the optional demo Caddy logs show DNS failures against `127.0.0.53` while contacting Let's Encrypt, recreate the stack after pulling this compose file. The demo compose pins container DNS to `1.1.1.1` and `8.8.8.8` to avoid EC2/systemd-resolved stub resolver issues inside containers.

## Demo URLs

Replace `EC2_PUBLIC_IP` and `YOUR_BP_API_KEY`:

```text
http://EC2_PUBLIC_IP:8000/api/health
http://EC2_PUBLIC_IP:8000/static/index.html?api_key=YOUR_BP_API_KEY
https://backpocket.himanshulade.com/api/health
https://backpocket.himanshulade.com/static/index.html?api_key=YOUR_BP_API_KEY
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
