# Deploying to AWS Lightsail

Cheapest plan (~$3.50-5/mo, often covered by AWS free-trial credit) gives you
enough RAM to run the whole Docker Compose stack. This satisfies the job
posting's "AWS / GCP / VPS" and "Deploy using Docker and cloud" points
directly.

## 1. Create the instance

1. AWS Console → Lightsail → **Create instance**.
2. Platform: Linux/Unix. Blueprint: **OS Only → Ubuntu 22.04**.
3. Pick the cheapest plan (1 GB RAM / 2 vCPU tier recommended if available —
   Qdrant + Postgres + Redis + Celery + n8n together want a bit more than the
   smallest 512 MB tier).
4. Name it (e.g. `whatsapp-ai-agent`) and create it.

## 2. Networking

1. Lightsail → your instance → **Networking** tab → attach a **static IP**.
2. Under the same tab, open firewall ports: **80** (HTTP) and **443** (HTTPS)
   in addition to the default 22 (SSH).

## 3. Get a free domain name for HTTPS

Meta requires the webhook URL to be HTTPS with a valid certificate — you need
a real hostname, not a bare IP. Two free options:

- **Free trick, zero setup**: use `sslip.io` — `<your-static-ip>.sslip.io`
  resolves automatically to that IP. E.g. if your static IP is
  `52.1.2.3`, use `52.1.2.3.sslip.io`. No DNS configuration needed.
- **Your own domain**: point an `A` record at the static IP instead.

## 4. Install Docker

SSH into the instance (Lightsail's browser SSH button works fine), then:

```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
# log out and back in for the group change to take effect
```

## 5. Deploy the app

```bash
git clone <your-repo-url> whatsapp-agent
cd whatsapp-agent
cp .env.example .env
nano .env   # fill in WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, GROQ_API_KEY, etc.
```

Edit `docker/Caddyfile` and replace `your-domain.com` with your
`sslip.io` hostname (or real domain) from step 3.

```bash
docker compose --profile prod up -d --build
```

This starts `api`, `worker`, `postgres`, `redis`, `qdrant`, and `caddy`
(auto-HTTPS reverse proxy on ports 80/443). Add `--profile with-n8n` too if
you want the n8n escalation workflow running on the same box.

Seed data:

```bash
docker compose exec api python -m scripts.seed_db
docker compose exec api python -m scripts.ingest_knowledge_base
```

## 6. Point Meta's webhook at your server

Meta app dashboard → WhatsApp → Configuration → Webhook:

- Callback URL: `https://<your-domain>/webhook`
- Verify token: whatever you set as `WHATSAPP_VERIFY_TOKEN` in `.env`
- Subscribe to the **messages** field.

Meta will call `GET /webhook` once to verify — Caddy's automatic TLS cert
needs a few seconds to issue on first request, so retry once if the first
verification attempt fails.

## 7. Confirm it's live

```bash
curl https://<your-domain>/health
```

Then message your WhatsApp test number from a verified recipient phone — you
should get a reply from the agent within a couple of seconds.

## Updating after a code change

```bash
git pull
docker compose --profile prod up -d --build
```

`unless-stopped` restart policies mean the stack also survives an instance
reboot automatically once Docker's systemd service is enabled (it is, by
default, after installing via `apt`).
