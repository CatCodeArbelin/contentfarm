# contentfarm

Contentfarm is a local automation stack for collecting source content, generating AI-assisted drafts, and approving or publishing them through a Telegram/n8n workflow.

## Services

The root `docker-compose.yml` starts the following services:

- `app` — FastAPI application container built from the repository `Dockerfile`.
- `postgres` — PostgreSQL 16 database for application and n8n persistence.
- `redis` — Redis 7 instance for queues, cache, and background coordination.
- `n8n` — workflow automation UI and webhook runtime.
- `ollama` — optional local LLM runtime used for draft generation when explicitly enabled with the `ollama` profile.
- `adminer` — optional database UI enabled with the `adminer` profile.

Persistent Docker volumes are defined for PostgreSQL, Redis, n8n, and optional Ollama data.

## Configuration

Create a local environment file from the example before starting the stack:

```bash
cp .env.example .env
```

Then edit `.env` and replace all placeholder secrets, especially:

- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `APP_SECRET_KEY`
- `WEBHOOK_API_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `N8N_ENCRYPTION_KEY`
- `N8N_BASIC_AUTH_PASSWORD`

## Start the stack

Start the core services in the background:

```bash
docker compose up -d
```

Start the stack with Adminer enabled:

```bash
docker compose --profile adminer up -d
```

Check service health and container status:

```bash
docker compose ps
```

Useful local URLs:

- FastAPI app: <http://localhost:8000>
- n8n: <http://localhost:5678>
- Ollama API, when running separately on the host or with the optional profile: <http://localhost:11434>
- Adminer, when profile is enabled: <http://localhost:8080>

## Database migrations

Run Alembic migrations after the containers are healthy:

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

## Ollama setup and draft generation

On Windows 11, install and start Ollama separately in Windows rather than running it inside Docker. The application defaults to connecting to the host Ollama API at `http://host.docker.internal:11434`; keep `OLLAMA_BASE_URL` set to that value unless you intentionally run Ollama elsewhere.

Pull the default recommended model before generating drafts:

```bash
ollama pull qwen2.5:14b
```

If your machine does not have enough memory for that model or you prefer another model, choose a different Ollama model, pull it with `ollama pull <model>`, and set `OLLAMA_MODEL=<model>` in `.env`.

Generate drafts with the configured Ollama model:

```bash
docker compose exec app python -m contentfarm.cli generate-drafts --model "$OLLAMA_MODEL"
```

The compose file still includes an optional `ollama` service for users who explicitly want Docker-managed Ollama. Start it with the `ollama` profile and then pull a model into that service:

```bash
docker compose --profile ollama up -d ollama
docker compose exec ollama ollama pull "${OLLAMA_MODEL:-qwen2.5:14b}"
```

## Approve and publish flow

1. The collector stores normalized source items in PostgreSQL and queues work in Redis.
2. Draft generation reads queued items, calls Ollama, and saves generated drafts with a `pending_review` status.
3. n8n receives draft-ready events from the app or polls the app API.
4. n8n sends each draft to the configured Telegram chat for review.
5. An editor approves, rejects, or requests changes from Telegram.
6. Approved drafts move to `approved`; rejected drafts stay archived with reviewer feedback.
7. The publish workflow posts approved drafts to the target channel or CMS and marks them as `published`.

Typical review command examples:

```text
/approve <draft_id>
/reject <draft_id> <reason>
/rewrite <draft_id> <instructions>
/publish <draft_id>
```

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
2. **HTTP Request: store raw item** — `POST http://app:8000/webhooks/raw-item` with JSON like:

   ```json
   {
     "source_id": 1,
     "title": "{{$json.title}}",
     "url": "{{$json.link}}",
     "content": "{{$json.contentSnippet || $json.content}}",
     "language": "en",
     "topic": "tech",
     "platform": "telegram",
     "strategy": "telegram_short",
     "status": "pending"
   }
   ```

3. **HTTP Request: generate draft** — after the item is deduplicated or matched to a news event, call `POST http://app:8000/webhooks/generate`:

   ```json
   {
     "news_event_id": 42,
     "strategy": "telegram_short",
     "language": "en",
     "platform": "telegram"
   }
   ```

4. **HTTP Request: prepare review notification** — call `POST http://app:8000/webhooks/review-notify` for the generated variant:

   ```json
   {
     "target_type": "variant",
     "target_id": 7,
     "admin_chat_id": "123456789"
   }
   ```

5. **Telegram node: send message** — send the `message` field returned by the previous node to the admin chat with HTML parse mode. The message includes approve, reject, and publish command templates.
6. **Telegram Trigger / approval branch** — when an editor approves the post, mark the variant or publication approved through the moderation API.
7. **HTTP Request: publish** — call `POST http://app:8000/webhooks/publish` only after approval:

   ```json
   {
     "target_type": "variant",
     "target_id": 7,
     "platform": "telegram"
   }
   ```

The publish webhook rejects anything that is not in `approved` status with `409 Conflict`, so n8n can safely retry or route non-approved posts back to the review branch.
