# Nginx + ngrok: Understanding Domain Exposure

## The Big Picture

In production, here's how a website becomes reachable:

```
User types example.com
        │
        ▼
DNS resolves example.com → 203.0.113.10 (your VM's public IP)
        │
        ▼
Traffic hits VM on port 80/443
        │
        ▼
Nginx receives the request, checks "server_name"
        │
        ▼
Nginx routes to the correct backend based on the domain
```

**ngrok simulates this entire chain locally.** It gives you a public URL (like `https://abc123.ngrok-free.app`) that tunnels traffic to your local nginx — just like a DNS record pointing a domain to your VM.

## How It Maps

| Production (VM)                        | Local (ngrok)                             |
|----------------------------------------|-------------------------------------------|
| Buy a domain (`example.com`)           | ngrok gives you a random subdomain        |
| Point DNS A record to VM's IP          | ngrok tunnel handles routing              |
| Nginx listens on port 80               | Nginx listens on port 8080                |
| `server_name example.com;`             | `server_name localhost;`                  |
| Users visit `https://example.com`      | Users visit `https://abc123.ngrok-free.app` |

## Why This Matters

On a VM, nginx is the **front door**. Without it:

- Your Flask app would need to listen on port 80 directly (requires root)
- You couldn't serve multiple domains from one server
- You'd have no SSL, no rate limiting, no caching
- Every backend would need its own public port

Nginx solves all of this. One process on port 80/443 routing traffic to any number of backends based on the domain name.

## Install ngrok

```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

Sign up for a free account at [ngrok.com](https://ngrok.com) and authenticate:

```bash
ngrok config add-authtoken <your-token>
```

## Basic Usage

```bash
# Expose local port 8080 to the internet
ngrok http 8080
```

ngrok prints a public URL like:

```
Forwarding  https://abc123.ngrok-free.app → http://localhost:8080
```

Anyone on the internet can now access your local nginx through that URL.

## server_name: The Domain Router

On a real VM, you'd have multiple `server` blocks for different domains:

```nginx
# /etc/nginx/conf.d/app1.conf
server {
    listen 80;
    server_name app1.example.com;
    location / {
        proxy_pass http://localhost:3000;
    }
}

# /etc/nginx/conf.d/app2.conf
server {
    listen 80;
    server_name app2.example.com;
    location / {
        proxy_pass http://localhost:4000;
    }
}
```

One VM, one nginx, one IP address — but two completely different apps served based on the domain in the request. This is called **virtual hosting**, and it's one of the main reasons nginx exists on every production server.
