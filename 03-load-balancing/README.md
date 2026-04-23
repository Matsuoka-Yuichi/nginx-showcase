# 03 - Load Balancing

## What You'll Learn

Nginx can distribute traffic across multiple backend instances. This scenario runs three copies of the same app, each identified by a unique `INSTANCE_ID`.

**Key directives:** `upstream`, `server` (within upstream), `weight`

## Start

```bash
docker compose up -d --build
```

## Smoke Test

```bash
curl http://localhost:8080/
```

## Concept Tests

**Round-robin in action — run 6 requests and watch the instance cycle:**

```bash
for i in $(seq 1 6); do
  curl -s http://localhost:8080/ | python3 -c "import sys,json; print(json.load(sys.stdin)['instance'])"
done
```

You should see `backend-1`, `backend-2`, `backend-3` repeating.

**Resilience — stop one backend and see traffic reroute:**

```bash
docker compose stop backend-2
for i in $(seq 1 4); do
  curl -s http://localhost:8080/ | python3 -c "import sys,json; print(json.load(sys.stdin)['instance'])"
done
docker compose start backend-2
```

Traffic now alternates between `backend-1` and `backend-3` only.

## Aha Moment

Run the curl loop, then stop a backend. Nginx automatically detects the failure and routes around it — no configuration change needed. Start it back up and it rejoins the pool.

## Tweak Exercises

1. In `nginx.conf`, uncomment the weighted `server` lines and comment out the equal ones. Reload and run the curl loop — backend-1 should appear ~3x more often
2. Add `ip_hash;` to the upstream block to enable sticky sessions — the same client always hits the same backend
3. Change the strategy to `least_conn;` and observe behavior

After any `nginx.conf` change:

```bash
docker compose exec nginx nginx -s reload
```

## Expose to the Internet with ngrok

> **Read [shared/ngrok-guide.md](../shared/ngrok-guide.md) first** for the full explanation of how ngrok maps to a real VM setup.

```bash
ngrok http 8080
```

Now have multiple people open the ngrok URL at the same time. Each person's request gets routed to a different backend instance — just like production.

**What this teaches about VMs:** On a real VM (or across multiple VMs), you'd run several copies of your app and use nginx's `upstream` block to distribute traffic. The outside world sees one domain, but behind nginx there could be 3, 10, or 100 backend instances. Scaling becomes invisible to clients:

```
Internet → domain → nginx → backend-1 :5000
                          → backend-2 :5000
                          → backend-3 :5000
```

**Try it:** Have a teammate repeatedly refresh the ngrok URL while you run `docker compose stop backend-2`. They'll never see an error — nginx silently reroutes to the healthy backends.

Stop ngrok with `Ctrl+C` when done.

## Teardown

```bash
docker compose down
```
