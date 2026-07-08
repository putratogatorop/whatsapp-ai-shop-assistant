# WhatsApp AI Shop Assistant

An AI-powered WhatsApp customer support & sales agent for a small online shop —
built as a portfolio project targeting **Junior AI Engineer (WhatsApp AI
Chatbot)** roles. It answers policy/product questions with RAG, takes orders
and checks stock through an LLM agent with tools, reads payment-proof
screenshots with OCR, and escalates to a human when it can't help.

## Why this project

Every item in the job posting maps to a real, working piece of this repo:

| Requirement | Where |
|---|---|
| Python, FastAPI, REST API | `app/main.py` — webhook + REST endpoints |
| Git & Docker | `docker/`, `docker-compose.yml` |
| LLM APIs (OpenAI, Claude, Gemini, ...) | `app/llm/factory.py` — pluggable, defaults to Groq's free tier |
| RAG & Vector DB (Qdrant) | `app/rag/` — fastembed + Qdrant |
| AI Agents (LangChain/LangGraph) | `app/agent/` — `create_react_agent` + tools |
| Connect to DB & external REST APIs | `app/db/`, `app/whatsapp/client.py` |
| Web scraping for knowledge base | `app/rag/scrape.py`, `scripts/ingest_knowledge_base.py --scrape` |
| Deploy with Docker + cloud | `DEPLOY.md` — AWS Lightsail |
| WhatsApp Business API | `app/whatsapp/` — Meta Cloud API |
| MCP | `app/mcp_server/server.py` |
| PostgreSQL / Redis | `app/db/session.py`, Celery broker |
| n8n | `app/integrations/n8n_notify.py` |
| OCR, Celery | `app/ocr/`, `app/workers/` |
| AWS / VPS | AWS Lightsail (see `DEPLOY.md`) |

## Architecture

```
WhatsApp user
     │  (message)
     ▼
Meta WhatsApp Cloud API
     │  webhook POST
     ▼
FastAPI  (app/main.py)
     │
     ├─ text message ─────► LangGraph agent (app/agent/graph.py)
     │                          │
     │                          ├─ search_knowledge_base ──► Qdrant (RAG)
     │                          ├─ check_stock / check_order_status ──► Postgres
     │                          ├─ create_order ──► Postgres
     │                          └─ escalate_to_human ──► n8n webhook
     │
     └─ image message (payment proof) ─► Celery task (app/workers/tasks.py)
                                              │
                                              ├─ download media from WhatsApp
                                              ├─ OCR (tesseract) ──► parse amount
                                              ├─ update order in Postgres
                                              └─ notify customer + n8n
```

Conversation history is persisted per customer in Postgres, so context
survives restarts and works across multiple worker processes.

## Tech stack

FastAPI · LangGraph · LangChain · Qdrant · fastembed · PostgreSQL · Redis ·
Celery · pytesseract · Meta WhatsApp Cloud API · Docker Compose · n8n (optional) · MCP

## Local setup

1. **Get WhatsApp Cloud API test credentials** (free, no business verification
   needed for testing):
   - Create an app at [developers.facebook.com](https://developers.facebook.com/apps) → add the **WhatsApp** product.
   - Under *API Setup* you get a temporary access token, a test phone number, and a `Phone Number ID`.
   - Add up to 5 personal WhatsApp numbers as verified recipients for testing.

2. **Get a free LLM API key** — [console.groq.com](https://console.groq.com) (default provider, free tier).

3. Copy the env file and fill in the values above:
   ```bash
   cp .env.example .env
   ```

4. Start everything:
   ```bash
   docker compose up -d --build
   ```

5. Seed sample products and the FAQ knowledge base:
   ```bash
   docker compose exec api python -m scripts.seed_db
   docker compose exec api python -m scripts.ingest_knowledge_base
   ```

6. Expose your local webhook to the internet for testing (e.g. `ngrok http 8000`),
   then in the Meta app dashboard set the webhook URL to
   `https://<your-ngrok-domain>/webhook`, the verify token to your
   `WHATSAPP_VERIFY_TOKEN`, and subscribe to the `messages` field.

7. Message your WhatsApp test number — you're talking to the agent.

For a persistent, real-domain deployment (no ngrok), see **[DEPLOY.md](DEPLOY.md)**
for the AWS Lightsail walkthrough.

## Environment variables

See `.env.example` for the full list with comments. Key one: `LLM_PROVIDER`
switches between `groq` (default, free), `openai`, `anthropic`, `gemini` — no
code changes needed.

## Running tests

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Bonus: MCP server

The same read-only tools (`search_knowledge_base`, `check_stock`,
`check_order_status`) are also exposed over MCP, independent of WhatsApp:

```bash
python -m app.mcp_server.server
```

Point any MCP client (Claude Desktop, `mcp inspector`, etc.) at this command
to query the shop's data directly.

## Project structure

```
app/
  main.py             FastAPI app: webhook verify/receive, health check
  config.py           Settings (env vars)
  whatsapp/           Meta Cloud API client + webhook parsing/signature verification
  llm/                Pluggable LLM provider factory
  agent/              LangGraph agent, tools, system prompt
  rag/                Embeddings (fastembed), Qdrant ingest/retrieve, scraper
  db/                 SQLAlchemy models, session, CRUD helpers
  ocr/                Payment-proof text/amount extraction
  workers/            Celery app + background tasks
  integrations/       n8n escalation webhook
  mcp_server/         MCP server exposing the same tools
data/faq_seed/        Seed knowledge-base documents (shipping, returns, payment, general)
scripts/              seed_db.py, ingest_knowledge_base.py
docker/               Dockerfile, Caddyfile
tests/                pytest suite
```
