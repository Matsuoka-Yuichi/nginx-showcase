# 05 - Rate Limiting

## What You'll Learn

Nginx can limit how many requests a client can make per second, protecting backends from abuse or accidental overload. This scenario configures two zones with different limits.

**Key directives:** `limit_req_zone`, `limit_req`, `burst`, `nodelay`

## Start

```bash
docker compose up -d --build
```

## Smoke Test

```bash
curl http://localhost:8080/
```

## Concept Tests

**Standard zone (5r/s) — send 20 rapid requests:**

```bash
for i in $(seq 1 20); do
  echo -n "Request $i: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
  echo
done
```

The first ~15 requests (5/s rate + 10 burst) return `200`, then you'll start seeing `503` responses.

**Strict zone (1r/s) — send 10 rapid requests to /health:**

```bash
for i in $(seq 1 10); do
  echo -n "Request $i: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health
  echo
done
```

Only ~4 requests succeed (1/s rate + 3 burst), the rest return `503`.

**See the custom error page:**

```bash
# First exhaust the burst allowance
for i in $(seq 1 20); do curl -s -o /dev/null http://localhost:8080/health; done
# Then see the error page
curl http://localhost:8080/health
```

## Aha Moment

Run the rapid curl loop and watch 200s turn into 503s in real time. Then wait a few seconds and try again — the limit resets and requests succeed again.

## Tweak Exercises

1. Change `rate=5r/s` to `rate=1r/s` in the standard zone, reload, and re-run the curl loop — limits kick in much sooner
2. Remove `nodelay` from a `limit_req` directive, reload, and observe that excess requests are now delayed (slower) instead of rejected
3. Increase `burst=10` to `burst=50` and see how many more requests get through

After any `nginx.conf` change:

```bash
docker compose exec nginx nginx -s reload
```

## Expose to the Internet with ngrok

> **Read [shared/ngrok-guide.md](../shared/ngrok-guide.md) first** for the full explanation of how ngrok maps to a real VM setup.

```bash
ngrok http 8080
```

Share the ngrok URL and have multiple people hit it rapidly. Since `limit_req_zone` uses `$binary_remote_addr` (client IP), each person gets their own rate limit bucket. But through ngrok, everyone might share the same IP — which means everyone competes for the same bucket.

**What this teaches about VMs:** Rate limiting is one of nginx's most important production roles. Without it, a single misbehaving client (or bot, or attacker) can overwhelm your backend. On a VM:

```
Internet → domain → nginx (rate limit per IP) → backend
                     ↳ legitimate user: 200 OK
                     ↳ abusive bot:     503 Rate Limited
```

The backend never sees the abusive traffic — nginx blocks it before it gets there.

**Try it:** Have a teammate spam-refresh the ngrok URL while you watch `docker compose logs -f nginx`. You'll see 503s appear as the rate limit kicks in.

Stop ngrok with `Ctrl+C` when done.

## Teardown

```bash
docker compose down
```
