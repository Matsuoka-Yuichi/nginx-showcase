# Nginx Gotchas

Common errors you'll hit when working with nginx, why they happen, and how to fix them properly.

---

## 1. `400 Bad Request — Request Header Or Cookie Too Large`

### What you see

```
400 Bad Request
Request Header Or Cookie Too Large
nginx/1.29.8
```

This typically happens in the browser but not with `curl`, which makes it confusing.

### Reproduce it

Use any running scenario (e.g., `01-static-files`). First, temporarily remove the buffer increase so you're testing against nginx's default 8KB limit:

**Step 1 — Remove `large_client_header_buffers` from `nginx.conf`** (comment it out or delete the line), then reload:

```bash
docker compose exec nginx nginx -s reload
```

**Step 2 — Send a request with a cookie bigger than 8KB:**

```bash
# 10,000-byte cookie — exceeds the 8KB default buffer
curl -H "Cookie: $(python3 -c "print('a' * 10000)")" http://localhost:8080/
```

You'll see:

```html
<html>
<head><title>400 Request Header Or Cookie Too Large</title></head>
<body>
<center><h1>400 Bad Request</h1></center>
<center>Request Header Or Cookie Too Large</center>
...
```

**Step 3 — Prove it works just under the limit:**

```bash
# 7,000-byte cookie — fits in the 8KB buffer (with room for other headers)
curl -H "Cookie: $(python3 -c "print('a' * 7000)")" http://localhost:8080/
```

This one returns 200.

**Step 4 — Add `large_client_header_buffers 4 16k;` back, reload, and retry the 10KB cookie:**

```bash
docker compose exec nginx nginx -s reload
curl -H "Cookie: $(python3 -c "print('a' * 10000)")" http://localhost:8080/
```

Now it returns 200 — the larger buffer handles it.

**Step 5 — Find the new limit:**

```bash
# 65,000 bytes — exceeds even 4x16k (64KB)
curl -H "Cookie: $(python3 -c "print('a' * 65000)")" http://localhost:8080/
```

400 again. The protection is still there, just with a higher threshold.

### Why it happens

Nginx allocates a small buffer (default: **1 x 8KB**) to read each incoming request's headers. If the combined size of all headers (including cookies) exceeds that buffer, nginx immediately rejects the request with a 400 — it never reaches your backend.

Your browser accumulates cookies for `localhost` from every project you've ever run locally (dev servers, other workshops, random tools). Over time these add up to tens of kilobytes. `curl` doesn't send cookies by default, so it works fine.

### Why nginx does this (it's a feature, not a bug)

This is a **deliberate security boundary**. Nginx handles thousands of concurrent connections, and each one needs a header buffer. Without a size limit:

- **Memory exhaustion** — an attacker sends thousands of connections with 1MB headers each, consuming all server RAM
- **Slowloris attacks** — oversized headers sent byte-by-byte tie up connections indefinitely
- **Abuse prevention** — legitimate HTTP requests rarely exceed 8KB of headers

Nginx's philosophy is: reject anything suspicious at the edge before it wastes backend resources. A huge header is suspicious by default.

### The fix

**Option A: Increase the buffer (server-side) — recommended**

Add `large_client_header_buffers` to your `server` block:

```nginx
server {
    listen 8080;
    server_name localhost;

    # Allow up to 4 buffers of 16KB each for request headers
    large_client_header_buffers 4 16k;

    # ... rest of config
}
```

- `4` = number of buffers
- `16k` = size of each buffer
- Total max header size = **64KB** (4 x 16k), which handles even the most cookie-heavy browsers

This is what our workshop configs use.

**Option B: Clear your cookies (client-side)**

Open your browser's dev tools → Application → Cookies → `localhost` → delete all. This is the quick fix but the cookies will accumulate again over time.

**Option C: Use a unique hostname instead of localhost**

Add an entry to `/etc/hosts`:

```
127.0.0.1  workshop.local
```

Then access `http://workshop.local:8080/` — fresh hostname, zero cookies.

### What NOT to do

Don't set the buffers absurdly large (e.g., `large_client_header_buffers 8 128k`) just to be safe. You'd be removing the security protection that makes this directive useful in the first place. **16k per buffer is generous enough for any legitimate browser request.**

### Production recommendation

In production, set a reasonable limit and let oversized requests fail:

```nginx
# Generous enough for real users, small enough to block abuse
large_client_header_buffers 4 16k;
```

If your application legitimately needs huge cookies (e.g., storing session data in cookies), the real fix is to move that data server-side (into a session store like Redis) and use a small session ID cookie instead.
