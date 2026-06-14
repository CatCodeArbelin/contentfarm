#!/usr/bin/env bash
set -euo pipefail

# Contentfarm MVP v0.1 smoke test.
# Requirements: curl. jq is recommended for parsing response IDs.
# Usage: BASE_URL=http://localhost:8000 API_PREFIX=/api/v1 ./scripts/smoke.sh

BASE_URL=${BASE_URL:-http://localhost:8000}
API_PREFIX=${API_PREFIX:-}
SMOKE_ID=${SMOKE_ID:-$(date +%s)}

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required by this smoke script to parse created IDs." >&2
  echo "Install jq or run the same curl commands manually from this script." >&2
  exit 1
fi

request() {
  local method=$1
  local path=$2
  local body=${3:-}

  if [[ -n "$body" ]]; then
    curl --fail-with-body --silent --show-error \
      --request "$method" \
      --header 'Content-Type: application/json' \
      --data "$body" \
      "$BASE_URL$API_PREFIX$path"
  else
    curl --fail-with-body --silent --show-error \
      --request "$method" \
      "$BASE_URL$API_PREFIX$path"
  fi
}

SOURCE_URL="https://example.com/contentfarm-smoke/source-$SMOKE_ID.xml"
RAW_ITEM_URL="https://example.com/contentfarm-smoke/raw-item-$SMOKE_ID"

echo "Smoke testing Contentfarm at $BASE_URL$API_PREFIX"

echo "==> GET /health"
request GET /health | tee /tmp/contentfarm_smoke_health.json

echo "==> POST /sources"
SOURCE_RESPONSE=$(request POST /sources "$(cat <<JSON
{
  "name": "Smoke Source $SMOKE_ID",
  "url": "$SOURCE_URL",
  "platform": "rss",
  "language": "en",
  "topic": "smoke",
  "strategy": "telegram_short",
  "status": "active"
}
JSON
)")
echo "$SOURCE_RESPONSE" | tee /tmp/contentfarm_smoke_source.json
SOURCE_ID=$(jq -r '.id' <<<"$SOURCE_RESPONSE")
echo "source_id=$SOURCE_ID"

echo "==> POST /raw-items"
RAW_ITEM_RESPONSE=$(request POST /raw-items "$(cat <<JSON
{
  "source_id": $SOURCE_ID,
  "title": "Smoke item $SMOKE_ID",
  "url": "$RAW_ITEM_URL",
  "content": "This smoke item verifies the MVP flow without requiring Telegram credentials. It should deduplicate into a news event and then be generated, approved, and exported as markdown.",
  "language": "en",
  "topic": "smoke",
  "platform": "telegram",
  "strategy": "telegram_short",
  "status": "pending"
}
JSON
)")
echo "$RAW_ITEM_RESPONSE" | tee /tmp/contentfarm_smoke_raw_item.json
RAW_ITEM_ID=$(jq -r '.id' <<<"$RAW_ITEM_RESPONSE")
echo "raw_item_id=$RAW_ITEM_ID"

echo "==> POST /news-events/deduplicate"
DEDUP_RESPONSE=$(request POST /news-events/deduplicate)
echo "$DEDUP_RESPONSE" | tee /tmp/contentfarm_smoke_deduplicate.json
NEWS_EVENT_ID=$(jq -r '.news_event_ids[0]' <<<"$DEDUP_RESPONSE")
echo "news_event_id=$NEWS_EVENT_ID"

echo "==> POST /generate/{news_event_id}"
GENERATE_RESPONSE=$(request POST "/generate/$NEWS_EVENT_ID")
echo "$GENERATE_RESPONSE" | tee /tmp/contentfarm_smoke_generate.json
VARIANT_ID=$(jq -r '.generated_variants[0].id' <<<"$GENERATE_RESPONSE")
echo "variant_id=$VARIANT_ID"

echo "==> GET /variants"
request GET /variants | tee /tmp/contentfarm_smoke_variants.json

echo "==> POST /variants/{variant_id}/approve"
APPROVE_RESPONSE=$(request POST "/variants/$VARIANT_ID/approve" '{"approved_by":"smoke"}')
echo "$APPROVE_RESPONSE" | tee /tmp/contentfarm_smoke_approve.json

echo "==> POST /publications/{variant_id}/export"
EXPORT_RESPONSE=$(request POST "/publications/$VARIANT_ID/export" '{"platform":"telegram","format":"markdown"}')
echo "$EXPORT_RESPONSE" | tee /tmp/contentfarm_smoke_export.json

echo "Smoke flow completed successfully."
