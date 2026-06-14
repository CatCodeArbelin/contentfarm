from fastapi import FastAPI

from app.api.routes import collectors, generation, metrics, moderation, news_events, publications, raw_items, sources, variants, workflow

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
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Contentfarm API",
        summary="Content collection, generation, moderation, and publication API.",
        description="API surface for managing the Contentfarm automation workflow.",
        version="0.1.0",
        openapi_tags=OPENAPI_TAGS,
        contact={"name": "Contentfarm maintainers"},
        license_info={"name": "MIT"},
    )

    app.include_router(sources.router, prefix="/api/v1")
    app.include_router(raw_items.router, prefix="/api/v1")
    app.include_router(news_events.router, prefix="/api/v1")
    app.include_router(generation.router, prefix="/api/v1")
    app.include_router(generation.generate_router)
    app.include_router(generation.generate_router, prefix="/api/v1")
    app.include_router(variants.router, prefix="/api/v1")
    app.include_router(publications.router, prefix="/api/v1")
    app.include_router(workflow.router)
    app.include_router(workflow.router, prefix="/api/v1")
    app.include_router(moderation.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")
    app.include_router(collectors.router, prefix="/api/v1")

    @app.get("/health", tags=["Health"], summary="Health check")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
