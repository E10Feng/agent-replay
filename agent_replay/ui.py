"""Rich-powered interactive REPL for AgentReplay."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agent_replay.inspector import StateInspector
from agent_replay.player import SessionPlayer

HELP_TEXT = """\
Commands:
  next | n          Advance to next checkpoint
  back | b          Go back to previous checkpoint
  jump <N>          Jump to checkpoint N (1-indexed)
  inspect           Show full state at current checkpoint
  diff              Show diff vs previous checkpoint
  search <query>    Find checkpoints containing query
  list              List all checkpoints with step/node
  help              Show this help message
  quit | q          Exit
"""


def _render_header(player: SessionPlayer) -> Panel:
    cp = player.current()
    step = cp.get("step", "?")
    node = cp.get("node", "unknown")
    title = Text(
        f"Step {player.position + 1} of {player.total}  —  Node: {node}  (step={step})",
        style="bold white",
    )
    return Panel(title, style="blue")


def run_session(
    player: SessionPlayer,
    inspector: StateInspector,
    console: Console,
) -> None:
    """Main REPL loop."""
    console.print(_render_header(player))
    console.print(inspector.format_state(player.current()))

    while True:
        try:
            raw = console.input("\n[bold cyan]>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nExiting.")
            break

        if not raw:
            continue

        parts = raw.split(None, 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("quit", "q"):
            console.print("Goodbye.")
            break

        elif cmd in ("next", "n"):
            cp, msg = player.next()
            if msg:
                console.print(f"[yellow]{msg}[/yellow]")
            console.print(_render_header(player))
            console.print(inspector.format_state(player.current()))

        elif cmd in ("back", "b"):
            cp, msg = player.back()
            if msg:
                console.print(f"[yellow]{msg}[/yellow]")
            console.print(_render_header(player))
            console.print(inspector.format_state(player.current()))

        elif cmd == "jump":
            if not arg:
                console.print("[red]Usage: jump <N>[/red]")
                continue
            try:
                n = int(arg)
            except ValueError:
                console.print("[red]N must be an integer[/red]")
                continue
            player.jump(n)
            console.print(_render_header(player))
            console.print(inspector.format_state(player.current()))

        elif cmd == "inspect":
            console.print(_render_header(player))
            console.print(inspector.format_state(player.current()))

        elif cmd == "diff":
            prev = player.previous()
            if prev is None:
                console.print("[yellow]No previous checkpoint to diff against.[/yellow]")
            else:
                console.print(inspector.diff(prev, player.current()))

        elif cmd == "search":
            if not arg:
                console.print("[red]Usage: search <query>[/red]")
                continue
            matches = player.search(arg)
            if not matches:
                console.print(f"[yellow]No matches for {arg!r}[/yellow]")
            else:
                console.print(f"[green]Found in checkpoints (0-indexed):[/green] {matches}")
                for idx in matches:
                    cp = player._checkpoints[idx]
                    console.print(
                        f"  [{idx + 1}] step={cp.get('step', '?')}  node={cp.get('node', 'unknown')}"
                    )

        elif cmd == "list":
            for i, cp in enumerate(player._checkpoints):
                marker = ">" if i == player.position else " "
                console.print(
                    f"  {marker} [{i + 1}] step={cp.get('step', '?')}  node={cp.get('node', 'unknown')}"
                )

        elif cmd == "help":
            console.print(HELP_TEXT)

        else:
            console.print(f"[red]Unknown command: {cmd!r}. Type 'help' for options.[/red]")
