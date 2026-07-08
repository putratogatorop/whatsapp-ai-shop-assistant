#!/usr/bin/env bash
# =============================================================================
# WhatsApp AI Shop Assistant — Lightsail Server Bootstrap
# =============================================================================
# Run ONCE on a fresh Ubuntu 24.04 box as root (this is injected as Lightsail
# instance user_data, so it normally runs automatically on first boot):
#
#   sudo bash server-bootstrap.sh
#
# The script is IDEMPOTENT — safe to re-run if interrupted. It installs
# Docker + the compose plugin (the whole app stack — api, worker, postgres,
# redis, qdrant, caddy — runs in containers, so unlike a bare Node/PM2 setup
# there's no system-level Caddy or language runtime to install here).
# =============================================================================
set -euo pipefail

LOGFILE="/var/log/whatsapp-agent-bootstrap.log"
exec > >(tee -a "$LOGFILE") 2>&1

echo "======================================================================"
echo "Bootstrap — $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "======================================================================"

# ── 1. System update ─────────────────────────────────────────────────────
echo ""
echo ">>> [1/6] Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y --no-install-recommends

# ── 2. Swap (2 GB) ───────────────────────────────────────────────────────
# The small_3_0 bundle has 2 GB RAM; a modest swap file is cheap insurance
# against OOM kills when Qdrant/Postgres/Celery all warm up at once.
echo ""
echo ">>> [2/6] Configuring 2 GB swap..."
if [ -f /swapfile ]; then
  echo "    /swapfile already exists — skipping creation."
else
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo "    Swap created and activated."
fi

if ! grep -q '/swapfile' /etc/fstab; then
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "    Added /swapfile to /etc/fstab."
fi

SWAPPINESS_CONF=/etc/sysctl.d/99-swap.conf
if [ ! -f "$SWAPPINESS_CONF" ]; then
  echo "vm.swappiness=10" > "$SWAPPINESS_CONF"
  sysctl --system -q
  echo "    vm.swappiness set to 10."
fi

# ── 3. Docker + Compose plugin ───────────────────────────────────────────
echo ""
echo ">>> [3/6] Installing Docker..."
if command -v docker &>/dev/null; then
  echo "    Docker already installed: $(docker --version)"
else
  apt-get install -y ca-certificates curl gnupg git
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  echo "    Docker installed: $(docker --version)"
fi

DEPLOY_USER="${SUDO_USER:-ubuntu}"
usermod -aG docker "$DEPLOY_USER"
systemctl enable --now docker
echo "    ${DEPLOY_USER} added to docker group, docker.service enabled."

# ── 4. Security hardening ────────────────────────────────────────────────
echo ""
echo ">>> [4/6] Installing fail2ban + unattended-upgrades..."
apt-get install -y fail2ban unattended-upgrades
systemctl enable --now fail2ban
dpkg-reconfigure -plow unattended-upgrades || true
systemctl enable --now unattended-upgrades
echo "    fail2ban + unattended-upgrades enabled."

# ── 5. Application directory ─────────────────────────────────────────────
echo ""
echo ">>> [5/6] Creating /opt/whatsapp-agent..."
mkdir -p /opt/whatsapp-agent
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" /opt/whatsapp-agent
echo "    /opt/whatsapp-agent — OK, owned by ${DEPLOY_USER}"

# ── 6. Done ───────────────────────────────────────────────────────────────
echo ""
echo ">>> [6/6] Bootstrap complete."

cat <<'NEXT_STEPS'

======================================================================
 Bootstrap complete. Manual steps required before first deploy:
======================================================================

1. AUTHORIZE YOUR DEPLOY SSH KEY (if not already added via Lightsail's
   own key-pair mechanism):
     mkdir -p ~/.ssh && chmod 700 ~/.ssh
     echo "<public-key>" >> ~/.ssh/authorized_keys
     chmod 600 ~/.ssh/authorized_keys

2. CLONE THE REPO
     cd /opt/whatsapp-agent
     git clone <your-repo-url> .

3. CREATE THE RUNTIME .env (contains secrets — never commit this)
     cp .env.example .env
     nano .env
     # Fill in WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, GROQ_API_KEY, etc.

4. POINT DUCKDNS AT THIS INSTANCE
   Register a subdomain at https://www.duckdns.org and point it at this
   box's static IP. Then edit infra/lightsail's referenced Caddyfile
   (docker/Caddyfile) to use that hostname instead of the placeholder.

5. FIRST DEPLOY
     docker compose --profile prod up -d --build
     docker compose exec api python -m scripts.seed_db
     docker compose exec api python -m scripts.ingest_knowledge_base

6. VERIFY
     curl https://<your-subdomain>.duckdns.org/health

======================================================================
NEXT_STEPS
