"""StateInspector: format and diff checkpoint state for display."""

from typing import Any


class StateInspector:
    """Format checkpoint state and produce diffs between checkpoints."""

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def format_state(self, checkpoint: dict) -> str:
        """
        Return a human-readable string representation of *checkpoint* state.

        Renders messages (human/ai/tool), tool calls, and any extra channel values.
        """
        lines: list[str] = []
        state = checkpoint.get("state", {})
        messages = state.get("messages", [])
        channel_values = state.get("channel_values", {})

        lines.append(f"[bold]Checkpoint:[/bold] {checkpoint.get('checkpoint_id', 'n/a')}")
        lines.append(f"[bold]Step:[/bold]       {checkpoint.get('step', '?')}")
        lines.append(f"[bold]Node:[/bold]       {checkpoint.get('node', 'unknown')}")
        lines.append("")

        if messages:
            lines.append("[bold underline]Messages[/bold underline]")
            for msg in messages:
                lines.append(_format_message(msg))
        else:
            lines.append("[dim](no messages)[/dim]")

        # Extra channel values (skip 'messages' — already rendered)
        extra = {k: v for k, v in channel_values.items() if k != "messages" and v is not None}
        if extra:
            lines.append("")
            lines.append("[bold underline]Channel Values[/bold underline]")
            for key, value in extra.items():
                lines.append(f"  [cyan]{key}[/cyan]: {value!r}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Diff
    # ------------------------------------------------------------------

    def diff(self, cp1: dict, cp2: dict) -> str:
        """
        Return a string showing what changed between *cp1* and *cp2*.

        Added messages are prefixed with '+', removed with '-'.
        """
        lines: list[str] = []
        lines.append(
            f"[bold]Diff[/bold] step {cp1.get('step', '?')} → step {cp2.get('step', '?')}"
        )
        lines.append("")

        msgs1 = _get_messages(cp1)
        msgs2 = _get_messages(cp2)

        ids1 = {_msg_id(m): m for m in msgs1}
        ids2 = {_msg_id(m): m for m in msgs2}

        all_ids = list(dict.fromkeys(list(ids1.keys()) + list(ids2.keys())))

        has_changes = False
        for mid in all_ids:
            if mid in ids1 and mid not in ids2:
                has_changes = True
                lines.append(f"[red]- {_format_message(ids1[mid])}[/red]")
            elif mid not in ids1 and mid in ids2:
                has_changes = True
                lines.append(f"[green]+ {_format_message(ids2[mid])}[/green]")
            else:
                # Present in both — check content change
                text1 = _msg_content(ids1[mid])
                text2 = _msg_content(ids2[mid])
                if text1 != text2:
                    has_changes = True
                    lines.append(f"[red]- {_format_message(ids1[mid])}[/red]")
                    lines.append(f"[green]+ {_format_message(ids2[mid])}[/green]")

        if not has_changes:
            lines.append("[dim](no message changes)[/dim]")

        # Also diff non-message channel values
        cv1 = {k: v for k, v in _get_channel_values(cp1).items() if k != "messages"}
        cv2 = {k: v for k, v in _get_channel_values(cp2).items() if k != "messages"}

        for key in set(list(cv1.keys()) + list(cv2.keys())):
            v1 = cv1.get(key)
            v2 = cv2.get(key)
            if v1 != v2:
                has_changes = True
                if v1 is None:
                    lines.append(f"[green]+ {key}: {v2!r}[/green]")
                elif v2 is None:
                    lines.append(f"[red]- {key}: {v1!r}[/red]")
                else:
                    lines.append(f"[red]- {key}: {v1!r}[/red]")
                    lines.append(f"[green]+ {key}: {v2!r}[/green]")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_messages(cp: dict) -> list[dict]:
    return cp.get("state", {}).get("messages", [])


def _get_channel_values(cp: dict) -> dict:
    return cp.get("state", {}).get("channel_values", {})


def _msg_id(msg: dict) -> str:
    return msg.get("id", id(msg))


def _msg_content(msg: dict) -> str:
    return str(msg.get("content", ""))


def _format_message(msg: dict) -> str:
    """Return a one-line (or brief multi-line) representation of a message."""
    msg_type = msg.get("type", "unknown")
    content = msg.get("content", "")
    tool_calls = msg.get("tool_calls", [])
    tool_call_id = msg.get("tool_call_id")

    if msg_type == "human":
        return f"  [bold blue]Human:[/bold blue] {content}"

    if msg_type == "ai":
        parts = [f"  [bold green]AI:[/bold green] {content}" if content else "  [bold green]AI:[/bold green]"]
        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("args", tc.get("arguments", {}))
            parts.append(f"    [yellow]tool_call:[/yellow] {name}({_format_args(args)})")
        return "\n".join(parts)

    if msg_type == "tool":
        header = f"  [bold magenta]Tool[/bold magenta]"
        if tool_call_id:
            header += f" [{tool_call_id}]"
        return f"{header}: {content}"

    return f"  [{msg_type}]: {content}"


def _format_args(args: Any) -> str:
    if isinstance(args, dict):
        return ", ".join(f"{k}={v!r}" for k, v in args.items())
    return str(args)
