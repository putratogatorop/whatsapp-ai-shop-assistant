# WhatsApp AI Shop Assistant — Lightsail Deployment Runbook

## Live instance

| | |
|---|---|
| Hostname | `tokobot-ai.duckdns.org` |
| Static IP | `13.229.12.199` |
| Instance name | `whatsapp-ai-agent` (Lightsail, `ap-southeast-1`, `small_3_0`) |
| SSH user | `ubuntu` |
| SSH key | `whatsapp-ai-agent-deploy` (Lightsail key pair) |

## Architecture

```
GitHub Actions (workflow_dispatch)
  └── SSH → git pull → docker compose --profile prod up -d --build
Lightsail (small_3_0: 2GB RAM / 2vCPU / 60GB SSD, ap-southeast-1)
  /opt/whatsapp-agent/         ← git checkout, deployed in place
  Docker Compose: api (8000) · worker (celery) · postgres · redis · qdrant · caddy (80/443)
DuckDNS: tokobot-ai.duckdns.org → 13.229.12.199 (static)
Caddy: auto-HTTPS (Let's Encrypt HTTP-01) → reverse_proxy → api:8000
```

Unlike a bare Node/PM2 deployment, the whole stack — including the reverse
proxy — runs in containers, so there's no system-level Caddy or language
runtime to install on the box. A deploy is just: pull the new code, rebuild
the changed images, restart.

## 1. Instance provisioning (already done)

```bash
aws lightsail import-key-pair --region ap-southeast-1 \
  --key-pair-name whatsapp-ai-agent-deploy \
  --public-key-base64 "$(cat whatsapp-ai-agent-deploy.pub)"

aws lightsail create-instances \
  --region ap-southeast-1 \
  --instance-names whatsapp-ai-agent \
  --availability-zone ap-southeast-1a \
  --blueprint-id ubuntu_24_04 \
  --bundle-id small_3_0 \
  --key-pair-name whatsapp-ai-agent-deploy \
  --user-data file://infra/lightsail/server-bootstrap.sh

aws lightsail allocate-static-ip --region ap-southeast-1 --static-ip-name whatsapp-ai-agent-ip
aws lightsail attach-static-ip --region ap-southeast-1 --static-ip-name whatsapp-ai-agent-ip --instance-name whatsapp-ai-agent

aws lightsail put-instance-public-ports --region ap-southeast-1 --instance-name whatsapp-ai-agent --port-infos \
  fromPort=22,toPort=22,protocol=TCP \
  fromPort=80,toPort=80,protocol=TCP \
  fromPort=443,toPort=443,protocol=TCP
```

`server-bootstrap.sh` ran automatically as `user_data` on first boot —
installs Docker, sets up 2 GB swap, enables fail2ban + unattended-upgrades,
creates `/opt/whatsapp-agent`.

> Note: this AWS account's Lightsail limit was maxed at 3 instances. The
> unused `Metabase` instance was snapshotted (`metabase-final-snapshot-*`,
> restorable from that snapshot) and deleted to free the slot.

## 2. DuckDNS (already done)

`tokobot-ai.duckdns.org` is registered and pointed at `13.229.12.199`. To
update the IP later if the instance is ever recreated:

```bash
DUCKDNS_SUBDOMAIN=tokobot-ai DUCKDNS_TOKEN=<your-token> bash infra/lightsail/duckdns-update.sh
```

Caddy obtains a Let's Encrypt certificate automatically on first request to
port 80/443 — no manual cert work needed.

## 3. First deploy

```bash
ssh -i whatsapp-ai-agent-deploy.pem ubuntu@13.229.12.199
sudo mkdir -p /opt/whatsapp-agent && sudo chown ubuntu:ubuntu /opt/whatsapp-agent
cd /opt/whatsapp-agent
git clone https://github.com/putratogatorop/whatsapp-ai-shop-assistant.git .
cp .env.example .env
nano .env   # fill in WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, GROQ_API_KEY, POSTGRES_PASSWORD, etc.

docker compose --profile prod up -d --build
docker compose exec api python -m scripts.seed_db
docker compose exec api python -m scripts.ingest_knowledge_base
```

## 4. Point Meta's webhook at it

Meta app dashboard → WhatsApp → Configuration → Webhook:
- Callback URL: `https://tokobot-ai.duckdns.org/webhook`
- Verify token: your `WHATSAPP_VERIFY_TOKEN`
- Subscribe to the `messages` field.

## GitHub Actions deploy (optional, manual-trigger)

`.github/workflows/deploy.yml` SSHes in and runs `git pull && docker compose
--profile prod up -d --build`. Required repo secrets:

| Secret | Value |
|---|---|
| `LIGHTSAIL_SSH_KEY` | Private key matching `whatsapp-ai-agent-deploy` |
| `LIGHTSAIL_HOST` | `13.229.12.199` |
| `LIGHTSAIL_USER` | `ubuntu` |
| `APP_HOSTNAME` | `tokobot-ai.duckdns.org` |

Trigger: GitHub → Actions tab → "Deploy to Lightsail" → Run workflow.

## Monitoring

```bash
ssh -i whatsapp-ai-agent-deploy.pem ubuntu@13.229.12.199
docker compose logs -f api
docker compose logs -f worker
docker compose ps
curl https://tokobot-ai.duckdns.org/health
```

## Rollback

```bash
ssh -i whatsapp-ai-agent-deploy.pem ubuntu@13.229.12.199
cd /opt/whatsapp-agent
git log --oneline -5
git checkout <previous-commit>
docker compose --profile prod up -d --build
```
