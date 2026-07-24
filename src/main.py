"""Application Bootstrap Entrypoint."""

from fastapi import FastAPI
from src.cli.main import app as cli_app

app = FastAPI(title="AI Shopping Assistant Scraper API")


@app.get("/health")
async def health_check() -> dict:
    """Verify database health."""
    from src.infrastructure.db.session import check_db_health
    db_health = await check_db_health()
    if db_health.get("status") == "healthy":
        return {"status": "healthy", "ping": True}
    return {"status": "unhealthy", "database": db_health}


if __name__ == "__main__":
    cli_app()
