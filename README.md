# Nginx Workshop

A hands-on workshop that teaches what problems nginx solves through self-contained Docker Compose scenarios. Spin up each scenario, experiment, tear it down, move to the next.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (v2+)
- `curl` (pre-installed on macOS/Linux)
- [ngrok](https://ngrok.com/download) (free account — for exposing scenarios to the internet)
- A text editor
- Basic terminal familiarity

## Learning Path

Work through the scenarios in order — each builds on concepts from the previous one.

| # | Scenario | What You'll Learn | Difficulty |
|---|----------|-------------------|------------|
| 01 | [Static File Serving](01-static-files/) | Serve HTML/CSS directly from nginx | Beginner |
| 02 | [Reverse Proxy](02-reverse-proxy/) | Put nginx in front of a backend API | Beginner |
| 03 | [Load Balancing](03-load-balancing/) | Distribute traffic across multiple backends | Intermediate |
| 04 | [SSL/TLS Termination](04-ssl-termination/) | Handle HTTPS at the nginx layer | Intermediate |
| 05 | [Rate Limiting](05-rate-limiting/) | Protect backends from too many requests | Intermediate |
| 06 | [Caching](06-caching/) | Cache backend responses for instant repeats | Intermediate |

## Quick Start

```bash
# Pick a scenario (e.g., 01-static-files)
cd 01-static-files

# Start it
docker compose up -d

# Test it
curl http://localhost:8080/

# Tear it down before starting the next one
docker compose down
```

## How Each Scenario Works

Every scenario follows the same pattern:

1. **`docker-compose.yml`** — defines the containers (nginx + optional backend)
2. **`nginx.conf`** — the nginx configuration you're learning about
3. **`README.md`** — instructions, smoke tests, concept tests, and tweak exercises

The general workflow:

```
Start scenario → Run smoke test → Run concept tests → Expose with ngrok → Try tweak exercises → Tear down
```

## Modifying Nginx Config

You don't need to restart containers to test config changes. After editing `nginx.conf`:

```bash
docker compose exec nginx nginx -s reload
```

This hot-reloads the configuration inside the running container.

## Exposing to the Internet with ngrok

Every scenario includes an "Expose with ngrok" section. This lets you share your local nginx with the internet — simulating what happens on a real VM with a public domain.

```bash
# After starting any scenario:
ngrok http 8080
```

Read **[shared/ngrok-guide.md](shared/ngrok-guide.md)** for a full explanation of how ngrok maps to production VM setups, and why nginx is the front door of every server.

**TL;DR:** On a VM, DNS points a domain to the server's IP, and nginx routes traffic to backends. ngrok does the same thing — gives you a public URL that tunnels to your local nginx.

## Port Conventions

All scenarios use **port 8080** on the host to avoid root permission issues. Scenario 04 (SSL) also exposes **port 8443** for HTTPS.

## Project Structure

```
nginx-showcase/
├── README.md                    ← You are here
├── shared/
│   ├── backend/                 ← Flask API used by scenarios 02-05
│   └── ngrok-guide.md           ← How ngrok maps to real VM setups
├── 01-static-files/             ← Pure nginx, no backend
├── 02-reverse-proxy/            ← Nginx → single backend
├── 03-load-balancing/           ← Nginx → 3 backends
├── 04-ssl-termination/          ← HTTPS + redirect
├── 05-rate-limiting/            ← Request throttling
└── 06-caching/                  ← Response caching (own slow backend)
```

## Troubleshooting

**Port already in use:**

```bash
# Stop any running scenario first
docker compose down

# Or check what's using port 8080
lsof -i :8080
```

**Container won't start:**

```bash
# Check logs
docker compose logs

# Rebuild after code changes
docker compose up -d --build
```

**400 Bad Request — "Request Header Or Cookie Too Large":**

This means your browser is sending more cookie/header data than nginx's default buffer allows (8KB). This is a deliberate security feature — nginx limits header sizes to prevent memory exhaustion attacks. Our configs set `large_client_header_buffers 4 16k` to handle typical browser cookies, but if you still hit this, clear your cookies for `localhost` in your browser.

**Nginx config syntax error:**

```bash
# Test config without restarting
docker compose exec nginx nginx -t
```
