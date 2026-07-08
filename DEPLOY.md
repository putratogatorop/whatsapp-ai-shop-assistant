# Deploying to AWS Lightsail

Live at **https://tokobot-ai.duckdns.org** — a Lightsail `small_3_0` instance
(2GB RAM / 2vCPU, ap-southeast-1) running the whole stack via Docker Compose,
with DuckDNS providing a free hostname for Caddy's automatic HTTPS. This
satisfies the job posting's "AWS / GCP / VPS" and "Deploy using Docker and
cloud" points directly.

**Full runbook: [infra/lightsail/README.md](infra/lightsail/README.md)** —
instance provisioning, DuckDNS setup, first deploy, GitHub Actions
auto-deploy, monitoring, and rollback.

Quick reference:

```bash
ssh -i whatsapp-ai-agent-deploy.pem ubuntu@13.229.12.199
cd /opt/whatsapp-agent
git pull
docker compose --profile prod up -d --build
```

Or trigger the `Deploy to Lightsail` GitHub Actions workflow (manual
`workflow_dispatch`) instead of SSHing in by hand.
