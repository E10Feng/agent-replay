"""Click CLI entry point for AgentReplay."""

import sys

import click
from rich.console import Console

from agent_replay.inspector import StateInspector
from agent_replay.loader import CheckpointLoader
from agent_replay.player import SessionPlayer
from agent_replay.ui import run_session


@click.group()
def cli():
    """AgentReplay — step through LangGraph agent sessions checkpoint by checkpoint."""


@cli.command()
@click.option("--thread-id", required=True, help="Thread ID to load.")
@click.option(
    "--db-url",
    default="sqlite:///checkpoints.sqlite",
    show_default=True,
    help="SQLite path or PostgreSQL URL.",
)
@click.option(
    "--raw",
    is_flag=True,
    default=False,
    help="Use raw SQLite access instead of the LangGraph API.",
)
def session(thread_id: str, db_url: str, raw: bool) -> None:
    """Start an interactive replay session for THREAD_ID."""
    console = Console()

    loader = CheckpointLoader(db_url=db_url, raw=raw)
    try:
        checkpoints = loader.load_session(thread_id)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)
    except Exception as exc:
        console.print(f"[red]Failed to load session:[/red] {exc}")
        sys.exit(1)

    player = SessionPlayer(checkpoints)
    inspector = StateInspector()
    run_session(player, inspector, console)
