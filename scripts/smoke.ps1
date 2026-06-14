# Contentfarm MVP v0.1 smoke test for Windows PowerShell.
# Requirements: PowerShell only; no jq or bash required.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1

param(
    [string]$BaseUrl = $(if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:8000" }),
    [string]$ApiPrefix = $(if ($env:API_PREFIX) { $env:API_PREFIX } else { "" }),
    [string]$SmokeId = $(if ($env:SMOKE_ID) { $env:SMOKE_ID } else { [DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString() })
)

$ErrorActionPreference = "Stop"

function Invoke-SmokeRequest {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Path,
        [object]$Body = $null
    )

    $uri = "$BaseUrl$ApiPrefix$Path"
    $parameters = @{
        Method = $Method
        Uri = $uri
    }

    if ($null -ne $Body) {
        $parameters.ContentType = "application/json"
        $parameters.Body = ($Body | ConvertTo-Json -Depth 10)
    }

    Invoke-RestMethod @parameters
}

function Write-SmokeJson {
    param([Parameter(Mandatory = $true)][object]$Value)

    $Value | ConvertTo-Json -Depth 20
}

$sourceUrl = "https://example.com/contentfarm-smoke/source-$SmokeId.xml"
$rawItemUrl = "https://example.com/contentfarm-smoke/raw-item-$SmokeId"

Write-Host "Smoke testing Contentfarm at $BaseUrl$ApiPrefix"

Write-Host "==> GET /health"
$healthResponse = Invoke-SmokeRequest -Method GET -Path "/health"
Write-SmokeJson $healthResponse

Write-Host "==> POST /sources"
$sourceResponse = Invoke-SmokeRequest -Method POST -Path "/sources" -Body @{
    name = "Smoke Source $SmokeId"
    url = $sourceUrl
    platform = "rss"
    language = "en"
    topic = "smoke"
    strategy = "short_news_post"
    status = "active"
}
Write-SmokeJson $sourceResponse
$sourceId = $sourceResponse.id
Write-Host "source_id=$sourceId"

Write-Host "==> POST /raw-items"
$rawItemResponse = Invoke-SmokeRequest -Method POST -Path "/raw-items" -Body @{
    source_id = $sourceId
    title = "Smoke item $SmokeId"
    url = $rawItemUrl
    content = "This smoke item verifies the MVP flow without requiring Telegram credentials. It should deduplicate into a news event and then be generated, approved, and exported as markdown."
    language = "en"
    topic = "smoke"
    platform = "telegram"
    strategy = "short_news_post"
    status = "pending"
}
Write-SmokeJson $rawItemResponse
$rawItemId = $rawItemResponse.id
Write-Host "raw_item_id=$rawItemId"

Write-Host "==> POST /news-events/deduplicate"
$dedupResponse = Invoke-SmokeRequest -Method POST -Path "/news-events/deduplicate"
Write-SmokeJson $dedupResponse
$newsEventId = $dedupResponse.news_event_ids[0]
Write-Host "news_event_id=$newsEventId"

Write-Host "==> POST /generate/{news_event_id}"
$generateResponse = Invoke-SmokeRequest -Method POST -Path "/generate/$newsEventId"
Write-SmokeJson $generateResponse
$variantId = $generateResponse.generated_variants[0].id
Write-Host "variant_id=$variantId"

Write-Host "==> GET /variants"
$variantsResponse = Invoke-SmokeRequest -Method GET -Path "/variants"
Write-SmokeJson $variantsResponse

Write-Host "==> POST /variants/{variant_id}/approve"
$approveResponse = Invoke-SmokeRequest -Method POST -Path "/variants/$variantId/approve" -Body @{
    approved_by = "smoke"
}
Write-SmokeJson $approveResponse

Write-Host "==> POST /publications/{variant_id}/export"
$exportResponse = Invoke-SmokeRequest -Method POST -Path "/publications/$variantId/export" -Body @{
    platform = "telegram"
    format = "markdown"
}
Write-SmokeJson $exportResponse

Write-Host "publication_id=$($exportResponse.id)"
Write-Host "export_path=$($exportResponse.export_path)"
Write-Host "Smoke completed!"
