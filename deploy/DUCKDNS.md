# Repeatify on DuckDNS

Production URL:

```text
https://repeatify.duckdns.org
```

The frontend is served from `/`, and the backend is proxied through `/api`.

## Frontend

Build on the server or locally:

```bash
cd frontend
npm ci
npm run build
sudo mkdir -p /var/www/repeatify
sudo rsync -a --delete dist/ /var/www/repeatify/
```

## Backend

Run FastAPI on localhost port `8000`:

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Production backend env should include:

```env
CORS_ORIGINS=https://repeatify.duckdns.org
```

## Reverse Proxy

Install Caddy, then copy `deploy/Caddyfile` to `/etc/caddy/Caddyfile` and reload:

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Caddy will issue and renew HTTPS certificates automatically.
