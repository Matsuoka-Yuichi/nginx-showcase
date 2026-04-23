# 02 - Reverse Proxy

## What You'll Learn

A reverse proxy sits between clients and backend servers. Clients talk to nginx, and nginx forwards requests to the backend. The backend is never exposed directly.

**Key directives:** `proxy_pass`, `proxy_set_header`

## Start

```bash
docker compose up -d --build
```

## Smoke Test

```bash
curl http://localhost:8080/
```

You should see a JSON response with `instance`, `hostname`, and `timestamp`.

## Concept Tests

**Verify proxy headers reach the backend:**

```bash
curl -s http://localhost:8080/ | python3 -m json.tool
```

**Confirm the backend port is NOT directly accessible:**

```bash
curl http://localhost:5000/
# This should fail — connection refused
```

The backend container has no published ports. It's only reachable through nginx.

**Check nginx is forwarding headers** (look at the nginx access log):

```bash
docker compose logs nginx
```

## Aha Moment

The backend is completely hidden behind nginx. Try `docker compose ps` — you'll see the backend has no port mappings. The only way in is through port 8080 via nginx.

## Tweak Exercises

1. Add a new `proxy_set_header` for a custom header (e.g., `X-Workshop: nginx-demo`) and check if the backend receives it
2. Change `proxy_pass` to point to a non-existent service and observe the error
3. Add a second `location /health` block that proxies to `/health` on the backend

After any `nginx.conf` change:

```bash
docker compose exec nginx nginx -s reload
```

## Expose to the Internet with ngrok

> **Read [shared/ngrok-guide.md](../shared/ngrok-guide.md) first** for the full explanation of how ngrok maps to a real VM setup.

```bash
ngrok http 8080
```

Open the public ngrok URL — you'll see the JSON response from the Flask backend. But notice: the backend itself is completely unreachable from outside. There's no way to bypass nginx and hit Flask directly.

**What this teaches about VMs:** This is the #1 reason nginx exists on production VMs. Your app runs on an internal port (e.g., `localhost:5000`), and nginx is the only process listening on the public port. On a VM it looks like:

```
Internet → domain DNS → VM public IP → nginx :80 → Flask :5000 (internal only)
```

Without nginx, you'd have to expose Flask directly on port 80, which means:
- No request buffering or connection handling
- No access logs at the gateway level
- No ability to add SSL, rate limiting, or caching later (the next scenarios)

**Try it:** Send the ngrok URL to a teammate. They can access the API but have no way to reach Flask's port 5000.

Stop ngrok with `Ctrl+C` when done.

## Teardown

```bash
docker compose down
```
