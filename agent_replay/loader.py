"""CheckpointLoader: fetch checkpoints from a LangGraph SQLite checkpoint store."""

import json
import sqlite3
from typing import Any


class CheckpointLoader:
    """Load LangGraph checkpoints from a SQLite store by thread_id."""

    def __init__(self, db_url: str = "sqlite:///checkpoints.sqlite", raw: bool = False):
        self.db_url = db_url
        self.raw = raw
        self._db_path = self._parse_db_path(db_url)

    def _parse_db_path(self, db_url: str) -> str:
        """Strip the sqlite:/// prefix to get the file path."""
        if db_url.startswith("sqlite:///"):
            return db_url[len("sqlite:///"):]
        return db_url

    def _decode_blob(self, blob: Any) -> dict:
        """Decode a checkpoint or metadata blob (JSON str or bytes)."""
        if isinstance(blob, bytes):
            try:
                return json.loads(blob.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        if isinstance(blob, str):
            try:
                return json.loads(blob)
            except json.JSONDecodeError:
                pass
        if isinstance(blob, dict):
            return blob
        return {}

    def _extract_node(self, metadata: dict) -> str:
        """Extract the node name from checkpoint metadata."""
        writes = metadata.get("writes")
        if writes and isinstance(writes, dict):
            keys = list(writes.keys())
            if keys:
                return keys[0]
        return "unknown"

    def load_session(self, thread_id: str) -> list[dict]:
        """
        Load all checkpoints for a thread_id from the SQLite store.

        Returns a list of checkpoint dicts ordered by step, each containing:
          thread_id, checkpoint_id, step, node, state, metadata
        Raises ValueError if no checkpoints found.
        """
        conn = sqlite3.connect(self._db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT checkpoint, metadata FROM checkpoints WHERE thread_id = ? ORDER BY rowid",
                (thread_id,),
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        if not rows:
            raise ValueError(f"No checkpoints found for thread_id: {thread_id!r}")

        results = []
        for checkpoint_blob, metadata_blob in rows:
            checkpoint_data = self._decode_blob(checkpoint_blob)
            metadata = self._decode_blob(metadata_blob)

            step = metadata.get("step", 0)
            node = self._extract_node(metadata)
            checkpoint_id = checkpoint_data.get("id", "")

            # Build a normalised state dict
            channel_values = checkpoint_data.get("channel_values", {})
            messages = channel_values.get("messages", [])

            state = {
                "messages": messages,
                "channel_values": channel_values,
            }

            results.append(
                {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id,
                    "step": step,
                    "node": node,
                    "state": state,
                    "metadata": metadata,
                }
            )

        # Sort by step
        results.sort(key=lambda c: c["step"])
        return results
