"""SessionPlayer: navigate a checkpoint sequence."""

from typing import Any


class SessionPlayer:
    """Wraps a list of checkpoints and manages the current position."""

    def __init__(self, checkpoints: list[dict]):
        if not checkpoints:
            raise ValueError("checkpoints list must not be empty")
        self._checkpoints = checkpoints
        self._index = 0

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def current(self) -> dict:
        """Return the checkpoint at the current position."""
        return self._checkpoints[self._index]

    def previous(self) -> dict | None:
        """Return the checkpoint before the current one, or None."""
        if self._index == 0:
            return None
        return self._checkpoints[self._index - 1]

    def next(self) -> tuple[dict, str]:
        """
        Advance to the next checkpoint.

        Returns (checkpoint, message).  If already at the last checkpoint,
        returns (last_checkpoint, "Already at end").
        """
        if self._index >= len(self._checkpoints) - 1:
            return self._checkpoints[self._index], "Already at end"
        self._index += 1
        return self._checkpoints[self._index], ""

    def back(self) -> tuple[dict, str]:
        """
        Go back to the previous checkpoint.

        Returns (checkpoint, message).  If already at the first checkpoint,
        returns (first_checkpoint, "Already at beginning").
        """
        if self._index <= 0:
            return self._checkpoints[self._index], "Already at beginning"
        self._index -= 1
        return self._checkpoints[self._index], ""

    def jump(self, n: int) -> dict:
        """
        Jump to 1-indexed position n.

        Clamps to valid range.  Returns the checkpoint at that position.
        """
        index = max(0, min(n - 1, len(self._checkpoints) - 1))
        self._index = index
        return self._checkpoints[self._index]

    def search(self, query: str) -> list[int]:
        """
        Search all checkpoints for query string.

        Returns a list of 0-indexed positions where query appears in the
        serialised checkpoint text (messages, tool names, channel values).
        """
        query_lower = query.lower()
        matches = []
        for i, cp in enumerate(self._checkpoints):
            text = _checkpoint_to_text(cp)
            if query_lower in text.lower():
                matches.append(i)
        return matches

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def position(self) -> int:
        """Current 0-indexed position."""
        return self._index

    @property
    def total(self) -> int:
        """Total number of checkpoints."""
        return len(self._checkpoints)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _checkpoint_to_text(cp: dict) -> str:
    """Flatten a checkpoint dict into a single searchable string."""
    import json
    try:
        return json.dumps(cp, default=str)
    except Exception:
        return str(cp)
