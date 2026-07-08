#!/usr/bin/env bash
# Keeps a DuckDNS subdomain pointed at this box's current public IP.
# Not strictly required with a Lightsail *static* IP (it never changes),
# but it's the standard DuckDNS pattern and a harmless safety net —
# e.g. if you ever move off a static IP.
#
# Usage:
#   DUCKDNS_SUBDOMAIN=whatsapp-ai-demo DUCKDNS_TOKEN=xxxx bash duckdns-update.sh
#
# To run on a schedule:
#   crontab -e
#   */5 * * * * DUCKDNS_SUBDOMAIN=whatsapp-ai-demo DUCKDNS_TOKEN=xxxx bash /opt/whatsapp-agent/infra/lightsail/duckdns-update.sh >> /var/log/duckdns.log 2>&1
set -euo pipefail

: "${DUCKDNS_SUBDOMAIN:?Set DUCKDNS_SUBDOMAIN}"
: "${DUCKDNS_TOKEN:?Set DUCKDNS_TOKEN}"

curl -fsS "https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip="
