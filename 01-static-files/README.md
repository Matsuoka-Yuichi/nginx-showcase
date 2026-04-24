# 01 - Static File Serving

## What You'll Learn

Nginx was originally built to serve static files fast. This scenario shows the most basic nginx setup — no backend, no application server, just HTML/CSS served directly by nginx.

**Key directives:** `server`, `listen`, `server_name`, `root`, `index`, `location`, `try_files`, `alias`, `autoindex`, `error_page`, `internal`

## Start

```bash
docker compose up -d
```

## The Config, Line by Line

Here's the full `nginx.conf` for this scenario. Every line is explained below.

```nginx
server {
    listen 8080;
    server_name localhost;

    large_client_header_buffers 4 16k;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /files/ {
        alias /usr/share/nginx/html/;
        autoindex on;
    }

    error_page 404 /404.html;
    location = /404.html {
        internal;
    }
}
```

### `server { ... }`

Everything lives inside a `server` block. One nginx process can have many `server` blocks — each one is a **virtual host**. When a request arrives, nginx picks the right `server` block based on the port and the `Host` header. This is how one VM can serve `app1.example.com` and `app2.example.com` from the same nginx.

### `listen 8080;`

Which port nginx listens on. We use 8080 to avoid needing root permissions (ports below 1024 require root on Linux). On a production VM, this would be `listen 80;` or `listen 443 ssl;`.

### `server_name localhost;`

Which domain name this server block responds to. Nginx matches the incoming `Host` header against this value. If you had two server blocks — one with `server_name app1.com;` and one with `server_name app2.com;` — nginx routes requests to the right one based on the domain.

For local development, `localhost` matches the `Host: localhost` header your browser sends.

### `large_client_header_buffers 4 16k;`

How much memory nginx allocates for reading request headers (including cookies). The default is 1 buffer of 8KB. We bump it to 4 buffers of 16KB because browsers accumulate cookies for `localhost` over time. See [Gotchas.md](../Gotchas.md) for the full story.

### `root /usr/share/nginx/html;`

The directory on disk where nginx looks for files. When a request comes in for `/about.html`, nginx looks for `/usr/share/nginx/html/about.html`. This is the filesystem path **inside the container** — our `docker-compose.yml` bind-mounts the `website/` folder to this path.

### `index index.html;`

When someone requests a directory (like `/`), nginx looks for this file inside that directory. So a request to `/` becomes `/usr/share/nginx/html/index.html`. You can list multiple files: `index index.html index.htm;` — nginx tries them in order.

### `location / { ... }`

A `location` block tells nginx how to handle requests matching a URL pattern. `location /` matches **everything** (it's the catch-all). More specific locations (like `/files/`) take priority over less specific ones.

Nginx evaluates locations in this order:
1. **Exact match** (`location = /path`) — highest priority
2. **Prefix match with `^~`** (`location ^~ /path`) — stops searching
3. **Regex match** (`location ~ /pattern`) — first regex wins
4. **Prefix match** (`location /path`) — longest prefix wins

### `try_files $uri $uri/ =404;`

This is the heart of static file serving. When a request comes in, nginx tries these in order:

1. `$uri` — look for a file matching the exact URL (e.g., `/about.html` → file `about.html`)
2. `$uri/` — look for a directory matching the URL (and serve its `index.html`)
3. `=404` — if neither exists, return a 404 error

Example: a request for `/style.css` → nginx checks if `style.css` exists → it does → serve it. A request for `/nonexistent` → no file, no directory → 404.

### `location /files/ { ... }`

A more specific location that matches any URL starting with `/files/`. Since this is more specific than `/`, nginx uses this block for those requests instead.

### `alias /usr/share/nginx/html/;`

`alias` vs `root` is one of the most confusing parts of nginx:

- **`root`** appends the full URL path to the directory. `root /data;` + request `/files/img.png` → looks for `/data/files/img.png`
- **`alias`** replaces the location prefix. `alias /data/;` + request `/files/img.png` → looks for `/data/img.png`

Here we use `alias` so that `/files/` maps to the same directory as `root` — it's a second entry point into the same folder, but with directory listing enabled.

### `autoindex on;`

When a request hits a directory and there's no `index.html` (or the `index` directive doesn't apply in this location), nginx normally returns 403 Forbidden. `autoindex on;` tells nginx to generate an HTML directory listing instead — like `ls` in a browser.

### `error_page 404 /404.html;`

When nginx would return a 404 status code, serve the file `/404.html` instead of the default nginx error page. In our setup, the 404 page lives in a separate directory (`error-pages/`), not in the web root — so it's not browsable as a normal file.

### `location = /404.html { root ...; internal; }`

Three things here:

- **`= /404.html`** — exact match location. Only matches the URL `/404.html` exactly, nothing else.
- **`root /usr/share/nginx/error-pages;`** — overrides the server-level `root` just for this location, pointing to the separate error pages directory.
- **`internal;`** — this location can only be reached via internal redirects (like `error_page`). Direct browser access is blocked.

**What happens when someone visits `/404.html` directly?**

1. Request matches `location = /404.html`
2. `internal` blocks it → nginx generates a 404 error
3. `error_page 404` catches that 404 → internal redirect back to `/404.html`
4. This time `internal` allows it (it's an internal redirect now) → custom page is served

So the user sees the custom 404 page **with a 404 status code**. The `internal` directive doesn't hide the content — it ensures the page is always served as an error, never as a normal 200 OK response. This is the correct production behavior: every path that doesn't exist should return 404, including `/404.html` itself.

You can verify the status code difference by temporarily removing `internal`:

```bash
# With internal (default): returns 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/404.html
# 404

# Without internal: would return 200 (served as a normal page)
```

## The Docker Compose File

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "8080:8080"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./website:/usr/share/nginx/html:ro
```

- **`image: nginx:alpine`** — official nginx image, Alpine-based (small)
- **`ports: "8080:8080"`** — maps host port 8080 to container port 8080
- **`./nginx.conf:/etc/nginx/conf.d/default.conf:ro`** — mounts our config into nginx's config directory. The `:ro` means read-only (the container can't modify it)
- **`./website:/usr/share/nginx/html:ro`** — mounts our `website/` folder as nginx's web root. This is why editing files on your host immediately shows up in the browser

Note: there is no `:ro` on the website volume in our actual file — we use `:ro` to show the concept, but removing it would let nginx write to the directory (not needed here).

## Smoke Test

```bash
curl http://localhost:8080/
```

You should see the HTML content of `index.html`.

## Concept Tests

**Serve different pages:**

```bash
curl http://localhost:8080/about.html
```

**Custom 404 page:**

```bash
curl http://localhost:8080/nonexistent
```

You should see the custom 404 page instead of nginx's default error.

**Prove `internal` works — the 404 page is never served as 200:**

```bash
# Direct access returns 404 status (not 200) — even though you see the custom page content
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/404.html
# 404

# A real page returns 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/about.html
# 200
```

The `internal` directive ensures `/404.html` can never be treated as a normal page.

**Directory listing (autoindex):**

```bash
curl http://localhost:8080/files/
```

This shows an HTML listing of all files in the website directory.

**Watch how nginx resolves `try_files`:**

```bash
# Matches a file directly
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/style.css
# 200

# Matches a directory (serves its index.html)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
# 200

# Matches nothing → falls through to =404
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/nope
# 404
```

## Aha Moment

Edit `website/index.html` on your host machine, save, and refresh your browser at `http://localhost:8080/`. The change appears instantly because the file is bind-mounted into the container — nginx reads it fresh from disk on every request.

## Tweak Exercises

1. **Change the default page:** Edit the `index` directive to `index about.html;`, reload, and visit `/` — it now serves the about page
2. **Disable directory listing:** Remove `autoindex on;`, reload, and visit `/files/` — you'll get 403 Forbidden
3. **Add a new page:** Create `website/contact.html`, add a link from `index.html`, and visit it — no config change or restart needed
4. **See `root` vs `alias` difference:** Change `alias /usr/share/nginx/html/;` to `root /usr/share/nginx/html;` in the `/files/` location, reload, and visit `/files/` — it will now look in `/usr/share/nginx/html/files/` (which doesn't exist)
5. **Remove `internal`:** Delete the `internal;` line, reload, and run `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/404.html` — now it returns `200` instead of `404` (the error page is served as a normal page)

After any `nginx.conf` change, reload without restarting:

```bash
docker compose exec nginx nginx -s reload
```

## Expose to the Internet with ngrok

> **Read [shared/ngrok-guide.md](../shared/ngrok-guide.md) first** for the full explanation of how ngrok maps to a real VM setup.

In a real VM, you'd point a domain (e.g., `mysite.com`) at the server's IP, and nginx would serve these static files to the world. ngrok simulates that:

```bash
ngrok http 8080
```

ngrok prints a public URL like `https://abc123.ngrok-free.app`. Share it — anyone on the internet can now see your static website, served by your local nginx.

**What this teaches about VMs:** On a production VM, nginx does the exact same thing. It listens on port 80, serves files from a directory (usually `/var/www/html`), and the domain's DNS record points to the VM's IP. No application server needed — just nginx and files.

**Try it:** Open the ngrok URL on your phone or send it to a teammate. They're seeing your local HTML files served through nginx.

Stop ngrok with `Ctrl+C` when done.

## Teardown

```bash
docker compose down
```
