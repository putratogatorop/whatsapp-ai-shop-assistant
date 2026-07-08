# WhatsApp AI Shop Assistant — Lightsail Deployment Runbook

## Architecture

```
GitHub Actions (workflow_dispatch)
  └── SSH → git pull → docker compose --profile prod up -d --build
Lightsail (small_3_0: 2GB RAM / 2vCPU / 60GB SSD, ap-southeast-1)
  /opt/whatsapp-agent/         ← git checkout, deployed in place
  Docker Compose: api (8000) · worker (celery) · postgres · redis · qdrant · caddy (80/443)
DuckDNS: <subdomain>.duckdns.org → Lightsail static IP
Caddy: auto-HTTPS (Let's Encrypt HTTP-01) → reverse_proxy → api:8000
```

Unlike a bare Node/PM2 deployment, the whole stack — including the reverse
proxy — runs in containers, so there's no system-level Caddy or language
runtime to install on the box. A deploy is just: pull the new code, rebuild
the changed images, restart.

## 1. Provision the instance

Already done via `aws lightsail create-instances` (see repo's deploy history /
`terraform` if you formalize this later, mirroring `MRA Apps/infra/terraform`).
Manual equivalent:

```bash
aws lightsail create-instances \
  --instance-names whatsapp-ai-agent \
  --availability-zone ap-southeast-1a \
  --blueprint-id ubuntu_24_04 \
  --bundle-id small_3_0 \
  --user-data file://infra/lightsail/server-bootstrap.sh \
  --key-pair-name <your-key-pair>

aws lightsail allocate-static-ip --static-ip-name whatsapp-ai-agent-ip
aws lightsail attach-static-ip --static-ip-name whatsapp-ai-agent-ip --instance-name whatsapp-ai-agent

aws lightsail put-instance-public-ports --instance-name whatsapp-ai-agent --port-infos \
  fromPort=22,toPort=22,protocol=TCP \
  fromPort=80,toPort=80,protocol=TCP \
  fromPort=443,toPort=443,protocol=TCP
```

`server-bootstrap.sh` runs automatically as `user_data` on first boot —
installs Docker, sets up 2 GB swap, enables fail2ban + unattended-upgrades,
creates `/opt/whatsapp-agent`.

## 2. DuckDNS setup

1. Log in at https://www.duckdns.org (free, GitHub/Google login) and register
   a subdomain, e.g. `whatsapp-ai-demo` → `whatsapp-ai-demo.duckdns.org`.
2. Point it at the Lightsail static IP from step 1 (paste the IP in the
   DuckDNS dashboard, or use `infra/lightsail/duckdns-update.sh`).
3. Edit `docker/Caddyfile` — replace `your-subdomain.duckdns.org` with your
   actual subdomain.
4. Caddy obtains a Let's Encrypt certificate automatically on first request
   to port 80/443 — no manual cert work.

## 3. First deploy

```bash
ssh ubuntu@<static-ip>
cd /opt/whatsapp-agent
git clone <your-repo-url> .          # or git pull if already cloned
cp .env.example .env
nano .env                             # fill in WHATSAPP_TOKEN, GROQ_API_KEY, etc.

docker compose --profile prod up -d --build
docker compose exec api python -m scripts.seed_db
docker compose exec api python -m scripts.ingest_knowledge_base
```

## 4. Point Meta's webhook at it

Meta app dashboard → WhatsApp → Configuration → Webhook:
- Callback URL: `https://<your-subdomain>.duckdns.org/webhook`
- Verify token: your `WHATSAPP_VERIFY_TOKEN`
- Subscribe to the `messages` field.

## GitHub Actions deploy (optional, manual-trigger)

`.github/workflows/deploy.yml` SSHes in and runs `git pull && docker compose
--profile prod up -d --build`. Required repo secrets:

| Secret | Description |
|---|---|
| `LIGHTSAIL_SSH_KEY` | Private key (PEM, no passphrase) matching a public key in the box's `~/.ssh/authorized_keys` |
| `LIGHTSAIL_HOST` | Static IP address |
| `LIGHTSAIL_USER` | `ubuntu` (default Lightsail Ubuntu user) |

Trigger: GitHub → Actions tab → "Deploy to Lightsail" → Run workflow.

## Monitoring

```bash
ssh ubuntu@<static-ip>
docker compose logs -f api
docker compose logs -f worker
docker compose ps
curl https://<your-subdomain>.duckdns.org/health
```

## Rollback

```bash
ssh ubuntu@<static-ip>
cd /opt/whatsapp-agent
git log --oneline -5
git checkout <previous-commit>
docker compose --profile prod up -d --build
```
