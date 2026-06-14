import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.routes import collectors, generation, metrics, moderation, news_events, publications, raw_items, sources, variants, webhooks, workflow

OPENAPI_TAGS = [
    {"name": "Sources", "description": "Source registry and ingestion configuration."},
    {"name": "RawItems", "description": "Collected raw content from configured sources."},
    {"name": "NewsEvents", "description": "Normalized event entities built from raw items."},
    {"name": "Generation", "description": "AI-assisted draft generation jobs."},
    {"name": "Variants", "description": "Platform-specific generated content variants."},
    {"name": "Publications", "description": "Publication queue and delivery status."},
    {"name": "Moderation", "description": "Editorial review decisions and audit trail."},
    {"name": "Metrics", "description": "Publication performance metrics."},
    {"name": "Collectors", "description": "Manual collection jobs for active sources."},
    {"name": "Webhooks", "description": "Shared-secret endpoints for n8n and external automation."},
]


def generate_operation_id(route: APIRoute) -> str:
    method = next(iter(sorted(route.methods or ["GET"]))).lower()
    path = route.path_format.strip("/").replace("/", "_").replace("{", "").replace("}", "").replace("-", "_")
    return f"{route.name}_{method}_{path or 'root'}"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Contentfarm API",
        summary="Content collection, generation, moderation, and publication API.",
        description="API surface for managing the Contentfarm automation workflow.",
        version="0.1.0",
        openapi_tags=OPENAPI_TAGS,
        contact={"name": "Contentfarm maintainers"},
        license_info={"name": "MIT"},
        generate_unique_id_function=generate_operation_id,
    )

    origins = [
        origin.strip()
        for origin in os.getenv("APP_CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(sources.router)
    app.include_router(sources.router, prefix="/api/v1")
    app.include_router(raw_items.router)
    app.include_router(raw_items.router, prefix="/api/v1")
    app.include_router(news_events.router)
    app.include_router(news_events.router, prefix="/api/v1")
    app.include_router(generation.router, prefix="/api/v1")
    app.include_router(generation.generate_router)
    app.include_router(generation.generate_router, prefix="/api/v1")
    app.include_router(variants.router)
    app.include_router(variants.router, prefix="/api/v1")
    app.include_router(publications.router)
    app.include_router(publications.router, prefix="/api/v1")
    app.include_router(publications.publish_router)
    app.include_router(publications.publish_router, prefix="/api/v1")
    app.include_router(webhooks.router)
    app.include_router(webhooks.router, prefix="/api/v1")
    app.include_router(workflow.router)
    app.include_router(workflow.router, prefix="/api/v1")
    app.include_router(moderation.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")
    app.include_router(collectors.router, prefix="/api/v1")

    operation_id_counts: dict[str, int] = {}
    for route in app.routes:
        if isinstance(route, APIRoute):
            method = next(iter(sorted(route.methods or ["GET"]))).lower()
            path = route.path.strip("/").replace("/", "_").replace("{", "").replace("}", "").replace("-", "_")
            base_operation_id = f"{route.name}_{method}_{path or 'root'}"
            operation_id_counts[base_operation_id] = operation_id_counts.get(base_operation_id, 0) + 1
            suffix = f"_{operation_id_counts[base_operation_id]}" if operation_id_counts[base_operation_id] > 1 else ""
            route.operation_id = f"{base_operation_id}{suffix}"

    @app.get("/health", tags=["Health"], summary="Health check")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
