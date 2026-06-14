# contentfarm

Contentfarm is a local automation stack for collecting source content, generating AI-assisted drafts, and approving or publishing them through a Telegram/n8n workflow.

## Services

The root `docker-compose.yml` starts the following services:

- `app` — FastAPI application container built from the repository `Dockerfile`.
- `postgres` — PostgreSQL 16 database for application and n8n persistence.
- `redis` — Redis 7 instance for queues, cache, and background coordination.
- `n8n` — workflow automation UI and webhook runtime.
- `ollama` — local LLM runtime used for draft generation.
- `adminer` — optional database UI enabled with the `adminer` profile.

Persistent Docker volumes are defined for PostgreSQL, Redis, n8n, and Ollama data.

## Configuration

Create a local environment file from the example before starting the stack:

```bash
cp .env.example .env
```

Then edit `.env` and replace all placeholder secrets, especially:

- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `APP_SECRET_KEY`
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
- Ollama API: <http://localhost:11434>
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

## Generate drafts

Generate drafts with the configured Ollama model:

```bash
docker compose exec app python -m contentfarm.cli generate-drafts --model "$OLLAMA_MODEL"
```

To preload a model into the Ollama volume, run:

```bash
docker compose exec ollama ollama pull "$OLLAMA_MODEL"
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
