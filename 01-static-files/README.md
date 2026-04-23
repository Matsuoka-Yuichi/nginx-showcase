# 01 - Static File Serving

## What You'll Learn

Nginx was originally built to serve static files fast. This scenario shows the most basic nginx setup — no backend, just HTML/CSS served directly.

**Key directives:** `root`, `location`, `index`, `try_files`, `autoindex`, `error_page`

## Start

```bash
docker compose up -d
```

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

**Directory listing (autoindex):**

```bash
curl http://localhost:8080/files/
```

This shows a listing of all files in the website directory.

## Aha Moment

Edit `website/index.html` on your host machine, save, and refresh your browser at `http://localhost:8080/`. The change appears instantly because the file is bind-mounted into the container.

## Tweak Exercises

1. Add a new HTML page and link to it from `index.html`
2. Change the `index` directive in `nginx.conf` to serve `about.html` as the default page
3. Disable `autoindex` and see what happens when you visit `/files/`

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
