"""CLI for running Orchestro Intelligence API server."""

import click
import uvicorn
from pathlib import Path


@click.group()
def api():
    """Orchestro Intelligence API server commands."""
    pass


@api.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind server to",
    show_default=True
)
@click.option(
    "--port",
    default=8000,
    help="Port to bind server to",
    show_default=True,
    type=int
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development"
)
@click.option(
    "--workers",
    default=1,
    help="Number of worker processes",
    show_default=True,
    type=int
)
@click.option(
    "--log-level",
    default="info",
    help="Logging level",
    show_default=True,
    type=click.Choice(["critical", "error", "warning", "info", "debug", "trace"])
)
def serve(host: str, port: int, reload: bool, workers: int, log_level: str):
    """Start the Orchestro Intelligence API server.

    Examples:
        # Development mode with auto-reload
        orchestro api serve --reload

        # Production mode with multiple workers
        orchestro api serve --workers 4 --log-level warning

        # Custom host and port
        orchestro api serve --host 127.0.0.1 --port 8080
    """
    click.echo("🚀 Starting Orchestro Intelligence API...")
    click.echo(f"📍 Server: http://{host}:{port}")
    click.echo(f"📚 Docs: http://{host}:{port}/docs")
    click.echo(f"🔍 GraphQL: http://{host}:{port}/graphql")

    uvicorn.run(
        "orchestro_cli.api.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,  # Workers don't work with reload
        log_level=log_level,
        access_log=True,
    )


@api.command()
def info():
    """Show API server information."""
    click.echo("Orchestro Intelligence API")
    click.echo("=" * 50)
    click.echo("Version: 0.2.1")
    click.echo("Description: REST/GraphQL API for automated CLI/TUI test generation")
    click.echo("")
    click.echo("Available Endpoints:")
    click.echo("  GET  /              - Root endpoint")
    click.echo("  GET  /health        - Health check")
    click.echo("  POST /api/v1/analyze    - Analyze application code")
    click.echo("  POST /api/v1/generate   - Generate test scenarios")
    click.echo("  GET  /api/v1/knowledge/{app_id} - Get cached knowledge")
    click.echo("  GET  /api/v1/jobs/{job_id}      - Get job status")
    click.echo("  DELETE /api/v1/jobs/{job_id}    - Cancel job")
    click.echo("  WS   /ws/analyze/{app_path}     - WebSocket analysis")
    click.echo("")
    click.echo("Documentation:")
    click.echo("  OpenAPI: /docs")
    click.echo("  ReDoc:   /redoc")
    click.echo("  GraphQL: /graphql")


if __name__ == "__main__":
    api()
