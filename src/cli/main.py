"""Typer CLI Command Application for Web Scraping Platform Management."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from src.config.settings import get_settings
from src.core.logging import setup_logging
from src.core.metrics import start_metrics_server
from src.engine.registry import CollectorRegistry
from src.infrastructure.db.base import Base
from src.infrastructure.db.session import check_db_health, close_db_engine, get_async_engine

app = typer.Typer(
    name="scraper-cli",
    help="AI Shopping Copilot Distributed Web Scraping Platform CLI",
    add_completion=False,
)

db_app = typer.Typer(help="Database management commands")
collector_app = typer.Typer(help="Collector & Parser plugin commands")
worker_app = typer.Typer(help="Worker execution pool commands")
system_app = typer.Typer(help="System status, observability, and health check commands")

app.add_typer(db_app, name="db")
app.add_typer(collector_app, name="collector")
app.add_typer(worker_app, name="worker")
app.add_typer(system_app, name="system")

console = Console()


@db_app.command("init")
def db_init() -> None:
    """Initialize database tables using SQLAlchemy DeclarativeBase metadata."""

    async def _init() -> None:
        settings = get_settings()
        setup_logging(settings.ENVIRONMENT, settings.LOG_LEVEL)
        console.print("[yellow]Initializing database schema...[/yellow]")
        try:
            engine = get_async_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            console.print("[bold green]Database schema initialized successfully![/bold green]")
        finally:
            await close_db_engine()

    asyncio.run(_init())


@db_app.command("check")
def db_check() -> None:
    """Check database connection health."""

    async def _check() -> None:
        settings = get_settings()
        setup_logging(settings.ENVIRONMENT, settings.LOG_LEVEL)
        try:
            health = await check_db_health()
            if health.get("status") == "healthy":
                console.print("[bold green]Database health status: HEALTHY[/bold green]")
            else:
                console.print(
                    f"[bold red]Database health status: UNHEALTHY - {health.get('error')}[/bold red]"
                )
        finally:
            await close_db_engine()

    asyncio.run(_check())


@collector_app.command("list")
def collector_list() -> None:
    """List all registered collectors and parsers."""
    CollectorRegistry.discover_plugins()
    sites = CollectorRegistry.list_sites()

    table = Table(title="Registered Site Collector Plugins")
    table.add_column("Site ID", style="cyan")
    table.add_column("Collector Class", style="magenta")
    table.add_column("Parser Class", style="green")

    for site in sites:
        collector_cls = CollectorRegistry.get_collector(site)
        try:
            parser_cls = CollectorRegistry.get_parser(site)
            parser_name = parser_cls.__name__
        except Exception:
            parser_name = "None"

        table.add_row(site, collector_cls.__name__, parser_name)

    console.print(table)


@collector_app.command("discover")
def collector_discover() -> None:
    """Trigger dynamic plugin auto-discovery scan inside src/collectors/."""
    count = CollectorRegistry.discover_plugins()
    console.print(
        f"[bold green]Auto-discovery completed. Registered {count} plugin(s).[/bold green]"
    )


@system_app.command("health")
def system_health() -> None:
    """Perform system health check across DB, Browser dependencies, and settings."""

    async def _health() -> None:
        settings = get_settings()
        setup_logging(settings.ENVIRONMENT, settings.LOG_LEVEL)

        table = Table(title="System Operational Health")
        table.add_column("Component", style="bold white")
        table.add_column("Status", style="bold cyan")
        table.add_column("Details", style="grey70")

        try:
            # Config check
            table.add_row("Configuration", "OK", f"Environment={settings.ENVIRONMENT}")

            # DB check
            db_res = await check_db_health()
            db_status = "OK" if db_res.get("status") == "healthy" else "ERROR"
            table.add_row("Database (PostgreSQL)", db_status, str(db_res))

            # Collectors check
            CollectorRegistry.discover_plugins()
            table.add_row(
                "Collector Plugins",
                "OK",
                f"Registered count = {len(CollectorRegistry.list_sites())}",
            )

            console.print(table)
        finally:
            await close_db_engine()

    asyncio.run(_health())


@worker_app.command("start")
def worker_start() -> None:
    """Start worker pool execution runtime."""
    settings = get_settings()
    setup_logging(settings.ENVIRONMENT, settings.LOG_LEVEL)

    if settings.PROMETHEUS_METRICS_ENABLED:
        start_metrics_server(settings.PROMETHEUS_METRICS_PORT)
        console.print(
            f"[cyan]Prometheus metrics exporter server running on port {settings.PROMETHEUS_METRICS_PORT}[/cyan]"
        )

    console.print(
        f"[bold green]Starting Scraper Runtime Worker Pool (Concurrency: {settings.WORKER_CONCURRENCY})...[/bold green]"
    )


if __name__ == "__main__":
    app()
