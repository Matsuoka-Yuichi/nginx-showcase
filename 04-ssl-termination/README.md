# 04 - SSL/TLS Termination

## What You'll Learn

Nginx handles HTTPS encryption so your backend doesn't have to. This is called "SSL termination" — encrypted traffic arrives at nginx, which decrypts it and forwards plain HTTP to the backend.

**Key directives:** `ssl_certificate`, `ssl_certificate_key`, `ssl_protocols`, `return 301`

## Prerequisites

Generate the self-signed certificate first:

```bash
cd certs
bash generate-certs.sh
cd ..
```

## Start

```bash
docker compose up -d --build
```

## Smoke Test

```bash
curl -k https://localhost:8443/
```

(`-k` tells curl to accept the self-signed certificate)

## Concept Tests

**HTTP automatically redirects to HTTPS:**

```bash
curl -v http://localhost:8080/ 2>&1 | grep "301\|Location"
```

You should see a `301 Moved Permanently` redirect to `https://localhost:8443/`.

**Inspect the certificate:**

```bash
echo | openssl s_client -connect localhost:8443 2>/dev/null | openssl x509 -noout -subject -issuer
```

You should see `O=Nginx Workshop` in the output.

**Backend receives plain HTTP (check X-Forwarded-Proto):**

```bash
curl -k -s https://localhost:8443/ | python3 -m json.tool
```

## Aha Moment

Visit `http://localhost:8080` in your browser — it automatically redirects to HTTPS. Click through the browser's certificate warning and inspect the cert details: you'll see the "Nginx Workshop" organization name from the generation script.

## Tweak Exercises

1. Modify `generate-certs.sh` to change the organization name, regenerate, and restart to see the new cert
2. Remove the HTTP redirect server block and verify that port 8080 no longer responds
3. Change `ssl_protocols` to only allow `TLSv1.3` and test with `curl --tlsv1.2` vs `curl --tlsv1.3`

After any `nginx.conf` change:

```bash
docker compose exec nginx nginx -s reload
```

## Expose to the Internet with ngrok

> **Read [shared/ngrok-guide.md](../shared/ngrok-guide.md) first** for the full explanation of how ngrok maps to a real VM setup.

For this scenario, expose the HTTP port so you can see the redirect chain:

```bash
ngrok http 8080
```

When someone visits the ngrok URL, nginx sends back a `301` redirect to HTTPS. However, the redirect points to `localhost:8443` (not the ngrok URL), so the external user won't be able to follow it. This is actually a great teaching moment.

**What this teaches about VMs:** In production, you'd set `server_name mysite.com;` and the redirect would go to `https://mysite.com` — which works because the domain resolves to the same VM. The self-signed cert would be replaced by a real one (e.g., from Let's Encrypt). The architecture:

```
Internet → https://mysite.com → nginx (terminates SSL) → http://flask:5000 (plain HTTP, internal)
```

The backend never deals with certificates, encryption, or HTTPS. Nginx handles it all. When it's time to renew a cert, you update it in one place (nginx) regardless of how many backends you have.

**Note:** ngrok itself provides HTTPS on the public URL. In production, you'd use nginx's SSL instead. This scenario teaches what nginx does; ngrok's own SSL is a shortcut for tunneling.

Stop ngrok with `Ctrl+C` when done.

## Teardown

```bash
docker compose down
```
