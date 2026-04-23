# 06 - Caching

## What You'll Learn

Nginx can cache backend responses so repeated requests are served instantly without hitting the backend again. This scenario uses a deliberately slow backend (2-second delay) to make caching effects obvious.

**Key directives:** `proxy_cache_path`, `proxy_cache`, `proxy_cache_valid`, `add_header`

## Start

```bash
docker compose up -d --build
```

## Smoke Test

```bash
curl http://localhost:8080/
```

## Concept Tests

**First request (MISS) — takes ~2 seconds:**

```bash
time curl -s -D - http://localhost:8080/slow | head -20
```

Look for `X-Cache-Status: MISS` in the headers. Note the response time (~2s).

**Second request (HIT) — instant:**

```bash
time curl -s -D - http://localhost:8080/slow | head -20
```

Now you'll see `X-Cache-Status: HIT` and the response is nearly instant.

**Compare with the non-cached endpoint:**

```bash
time curl -s http://localhost:8080/fast
time curl -s http://localhost:8080/fast
```

Both requests are fast (no artificial delay), but there's no `X-Cache-Status` header — these aren't cached.

**Watch the cache expire (wait 30s):**

```bash
# After waiting 30 seconds for the cache to expire:
time curl -s -D - http://localhost:8080/slow | head -20
```

You'll see `MISS` again and the 2-second delay returns.

## Aha Moment

The first `/slow` request takes a full 2 seconds. Hit it again immediately — it's instant. The `X-Cache-Status` header proves nginx served it from cache without touching the backend.

## Tweak Exercises

1. Change `proxy_cache_valid 200 30s` to `200 5m` (5 minutes), reload, and verify the cache lasts longer
2. Add `proxy_cache_bypass $http_x_no_cache;` and test with `curl -H "X-No-Cache: 1" http://localhost:8080/slow` to bypass the cache on demand
3. Add caching to the `/` location block and observe the difference

After any `nginx.conf` change:

```bash
docker compose exec nginx nginx -s reload
```

## Expose to the Internet with ngrok

> **Read [shared/ngrok-guide.md](../shared/ngrok-guide.md) first** for the full explanation of how ngrok maps to a real VM setup.

```bash
ngrok http 8080
```

Have a teammate open `<ngrok-url>/slow` — it takes 2 seconds. Now you open the same URL — it's instant. Nginx served the cached response without touching the backend.

**What this teaches about VMs:** Caching is where nginx really shines in production. Imagine an API endpoint that queries a database and takes 500ms. Without caching, 1000 users = 1000 database queries. With nginx caching, 1000 users = 1 database query + 999 instant cache hits:

```
Internet → domain → nginx (cache layer) → backend (only on MISS)
                     ↳ HIT:  instant response from disk/memory
                     ↳ MISS: forward to backend, cache the response
```

This is especially powerful for endpoints that return the same data for all users (product listings, public APIs, config endpoints).

**Try it:** Both you and a teammate visit `<ngrok-url>/slow`. Check the response headers — one of you will see `X-Cache-Status: MISS` (2s wait) and the other will see `HIT` (instant).

Stop ngrok with `Ctrl+C` when done.

## Teardown

```bash
docker compose down
```
