# contentfarm

Contentfarm is a local automation stack for collecting source content, deduplicating raw items into news events, generating AI-assisted variants, and approving, publishing, or exporting them.

## MVP v0.1 local flow

The MVP v0.1 flow is designed for Windows 11 with Docker Desktop running the application stack and Ollama running natively on the Windows host.

### 1. Install prerequisites

1. Install Docker Desktop for Windows and enable the WSL2 backend.
2. Install Ollama natively in Windows and make sure it is running.
3. Pull the recommended local model:

   ```bash
   ollama pull qwen2.5:14b
   ```

   To use another model instead, pull it with `ollama pull <model>` and set `OLLAMA_MODEL=<model>` in `.env`.

### 2. Configure the environment

Copy the example environment file and edit the local copy:

```bash
cp .env.example .env
```

At minimum, fill the Telegram values used by the MVP publish path:

- `TELEGRAM_BOT_TOKEN` — your Telegram bot token.
- `TELEGRAM_CHANNEL_ID` — the target channel or chat ID used when publishing to Telegram.

Also replace any other placeholder secrets before using the stack beyond local testing, including database, Redis, app, webhook, and n8n secrets.

Keep `OLLAMA_BASE_URL=http://host.docker.internal:11434` when Ollama is installed on Windows. That is how the Dockerized app reaches the Ollama API running on the Windows host.

### 3. Start the stack and migrate the database

Build and start the local services:

```bash
docker compose up -d --build
```

By default, Alembic migrations are applied automatically when the `app` container starts (`AUTO_MIGRATE=true` in `.env`). To disable automatic migrations and run them manually, set `AUTO_MIGRATE=false` in `.env`.

The manual migration command remains useful as an optional/debug command:

```bash
docker compose exec app alembic upgrade head
```

Check the app health endpoint:

```text
http://localhost:8000/health
```

Open the interactive API docs:

```text
http://localhost:8000/docs
```

### 4. Walk through the MVP in the API docs

Use <http://localhost:8000/docs> to run the local workflow end to end:

1. **Create a source** with `POST /api/v1/sources`.
2. **Create a raw item** with `POST /api/v1/raw-items`, using the source ID from the previous step.
3. **Deduplicate pending raw items** with `POST /api/v1/news-events/deduplicate`; this creates or updates a news event.
4. **Generate variants** with `POST /api/v1/generate/{news_event_id}`. This is the primary MVP v0.1 generation path and synchronously creates variants for the selected news event.

   `POST /api/v1/generation` only creates a generation `Job` record for future async job/queue support; it does not generate variants and is not the main MVP path.
5. **Approve the variant** with `POST /api/v1/variants/{variant_id}/approve`.
6. **Publish or export the approved variant**:
   - Publish to Telegram with `POST /api/v1/publications/{variant_id}/publish-telegram`.
   - Export markdown or HTML with `POST /api/v1/publications/{variant_id}/export`.

## Smoke test

After the stack is running and migrations are applied automatically, run the scripted MVP flow:

On Windows, prefer the PowerShell smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
```

On Git Bash, Linux, or WSL, use the Bash smoke test:

```bash
chmod +x scripts/smoke.sh
./scripts/smoke.sh
```

Both scripts create a source, raw item, news event, generated variant, approval, and markdown export. The Windows `scripts/smoke.ps1` script uses PowerShell `Invoke-RestMethod` and does not require `jq` or Bash. The `scripts/smoke.sh` script is intended for Git Bash, Linux, or WSL and uses `curl` and `jq`; if `jq` is not installed, install it or copy the commented curl commands from `scripts/smoke.sh` and run them manually.

## Services

The root `docker-compose.yml` starts the following services:

- `app` — FastAPI application container built from the repository `Dockerfile`.
- `frontend` — Next.js App Router frontend with TypeScript and Tailwind CSS, served on port 3000.
- `postgres` — PostgreSQL 16 database for application and n8n persistence.
- `redis` — Redis 7 instance for queues, cache, and background coordination.
- `n8n` — workflow automation UI and webhook runtime.
- `adminer` — optional database UI enabled with the `adminer` profile.
- `ollama` — optional Docker-managed LLM runtime enabled only with the `ollama` profile. For MVP v0.1 on Windows 11, prefer native Windows Ollama instead.

Persistent Docker volumes are defined for PostgreSQL, Redis, n8n, and optional Docker-managed Ollama data.

Useful local URLs:

- Frontend: <http://localhost:3000>
- FastAPI app: <http://localhost:8000>
- API health check: <http://localhost:8000/health>
- API docs: <http://localhost:8000/docs>
- n8n: <http://localhost:5678>
- Host Ollama API: <http://localhost:11434>
- Adminer, when profile is enabled: <http://localhost:8080>

## Optional profiles

Start the stack with Adminer enabled:

```bash
docker compose --profile adminer up -d
```

### Optional Docker-managed Ollama profile

The compose file includes an optional `ollama` service for users who explicitly want Docker-managed Ollama instead of the recommended native Windows Ollama setup. Start it with the `ollama` profile and pull a model into that service:

```bash
docker compose --profile ollama up -d ollama
docker compose exec ollama ollama pull "${OLLAMA_MODEL:-qwen2.5:14b}"
```

If you use this optional profile, point the app at the Docker service instead of the Windows host by setting this in `.env` before starting the app:

```env
OLLAMA_BASE_URL=http://ollama:11434
```

## Frontend

The `frontend/` directory contains the initial Next.js App Router scaffold for the future Contentfarm web interface. It uses TypeScript, Tailwind CSS, and dark mode by default. The current page is intentionally a Russian-language placeholder: it does not connect to real APIs and does not implement a dashboard.

Run it through Docker Compose with the rest of the local stack:

```bash
docker compose up -d --build frontend
```

Or run it directly from the `frontend/` directory during local UI development:

```bash
npm install
npm run dev
```

Copy `frontend/.env.example` if you need local frontend-specific overrides. The default local URL is <http://localhost:3000>.

## Database migrations

Alembic migrations run automatically at `app` container startup by default for the local MVP (`AUTO_MIGRATE=true`). To disable this behavior and manage migrations manually, set `AUTO_MIGRATE=false` in `.env`.

Optional/debug manual migration command:

```bash
docker compose exec app alembic upgrade head
```

Create a new migration after changing SQLAlchemy models:

```bash
docker compose exec app alembic revision --autogenerate -m "describe change"
```

Review the generated migration, then apply it:

```bash
docker compose exec app alembic upgrade head
```

## Run the collector

Use the application container so the collector has the same environment and network access as production:

```bash
docker compose exec app python -m contentfarm.collector
```

If the collector is exposed as a FastAPI or Typer command in your implementation, use the matching application command instead, for example:

```bash
docker compose exec app python -m contentfarm.cli collect
```

## Draft generation from the CLI

The MVP flow can be completed from the API docs, but the application can also generate drafts from the configured Ollama model with the CLI when available:

```bash
docker compose exec app python -m contentfarm.cli generate-drafts --model "$OLLAMA_MODEL"
```

## Approve and publish flow

1. Sources describe where content comes from.
2. Raw items store collected or manually entered source material.
3. Deduplication groups raw items into news events.
4. Generation calls Ollama and saves variants with review status.
5. An editor approves, rejects, or updates variants.
6. Approved variants can be published to Telegram or exported as markdown or HTML.

## Stop the stack

Stop containers while keeping data volumes:

```bash
docker compose down
```

Remove containers and persistent local data volumes:

```bash
docker compose down -v
```

## n8n webhook workflow example

The app exposes shared-secret webhook endpoints for n8n at both `/webhooks/*` and `/api/v1/webhooks/*`. Configure n8n HTTP Request nodes with either an `X-Webhook-Token: $WEBHOOK_API_TOKEN` header or an `Authorization: Bearer $WEBHOOK_API_TOKEN` header. The app reads `WEBHOOK_API_TOKEN` first and falls back to `APP_SECRET_KEY` when a dedicated webhook token is not set.

Example RSS-to-publish workflow:

1. **RSS Feed Trigger** — watches a feed and emits each RSS item.
2. **HTTP Request: store raw item** — `POST http://app:8000/webhooks/raw-item` saves the raw item with JSON like:

   ```json
   {
     "source_id": 1,
     "title": "{{$json.title}}",
     "url": "{{$json.link}}",
     "content": "{{$json.contentSnippet || $json.content}}",
     "language": "en",
     "topic": "tech",
     "platform": "telegram",
     "strategy": "short_news_post",
     "status": "pending"
   }
   ```

3. **HTTP Request: deduplicate** — call `POST http://app:8000/news-events/deduplicate` or `POST http://app:8000/api/v1/news-events/deduplicate` to create or update a news event from pending raw items.
4. **HTTP Request: generate variants** — call `POST http://app:8000/webhooks/generate`; for MVP v0.1 this synchronously creates variants and returns `generated_variants`:

   ```json
   {
     "news_event_id": 42,
     "strategy": "short_news_post",
     "language": "en",
     "platform": "telegram"
   }
   ```

5. **HTTP Request: prepare review notification** — call `POST http://app:8000/webhooks/review-notify` for the generated variant:

   ```json
   {
     "target_type": "variant",
     "target_id": 7,
     "admin_chat_id": "123456789"
   }
   ```

6. **Telegram node: send message** — send the `message` field returned by the previous node to the admin chat with HTML parse mode. The message includes approve, reject, and publish command templates.
7. **Telegram Trigger / approval branch** — when an editor approves the post, mark the variant approved with `POST /variants/{variant_id}/approve` or `POST /api/v1/variants/{variant_id}/approve`.
8. **HTTP Request: publish** — call `POST http://app:8000/webhooks/publish` only after approval:

   ```json
   {
     "target_type": "variant",
     "target_id": 7,
     "platform": "telegram"
   }
   ```

For MVP v0.1, `/webhooks/publish` supports only `target_type: "variant"`. Requests with `target_type: "publication"` return `400 Bad Request`; use variant targets after approval. The publish webhook rejects variants that are not in `approved` status with `409 Conflict`, so n8n can safely retry or route non-approved posts back to the review branch.
