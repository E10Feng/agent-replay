"""
create_sample_session.py
Creates checkpoints.sqlite in the current working directory with a sample
5-step weather-agent session under thread_id 'example-thread-001'.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


THREAD_ID = "example-thread-001"
DB_PATH = Path("checkpoints.sqlite")


def make_checkpoint(step: int, node: str, messages: list[dict]) -> tuple[str, str, str]:
    """Return (checkpoint_id, checkpoint_json, metadata_json)."""
    cp_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    checkpoint = {
        "v": 1,
        "ts": ts,
        "id": cp_id,
        "channel_values": {
            "messages": messages,
            "__start__": None,
        },
        "channel_versions": {},
        "versions_seen": {},
        "pending_sends": [],
    }

    writes = {node: None} if node != "unknown" else None
    metadata = {
        "step": step,
        "source": "input" if step == 0 else "loop",
        "writes": writes,
        "parents": {},
    }

    return cp_id, json.dumps(checkpoint), json.dumps(metadata)


def create_sample_session(db_path: Path = DB_PATH) -> None:
    """Write 5 checkpoints to db_path."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS checkpoints (
            thread_id            TEXT,
            checkpoint_ns        TEXT DEFAULT '',
            checkpoint_id        TEXT,
            parent_checkpoint_id TEXT,
            type                 TEXT DEFAULT 'json',
            checkpoint           BLOB,
            metadata             BLOB
        )
        """
    )

    # Remove any existing rows for this thread
    conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (THREAD_ID,))

    steps = [
        # step 0: user asks about weather
        (
            "__start__",
            [
                {
                    "type": "human",
                    "content": "What's the weather in Chicago?",
                    "id": "msg-0001",
                    "tool_calls": [],
                    "tool_call_id": None,
                }
            ],
        ),
        # step 1: AI decides to call get_weather tool
        (
            "agent",
            [
                {
                    "type": "human",
                    "content": "What's the weather in Chicago?",
                    "id": "msg-0001",
                    "tool_calls": [],
                    "tool_call_id": None,
                },
                {
                    "type": "ai",
                    "content": "",
                    "id": "msg-0002",
                    "tool_calls": [
                        {
                            "name": "get_weather",
                            "args": {"city": "Chicago"},
                            "id": "tc-abc123",
                        }
                    ],
                    "tool_call_id": None,
                },
            ],
        ),
        # step 2: tool returns weather result
        (
            "tools",
            [
                {
                    "type": "human",
                    "content": "What's the weather in Chicago?",
                    "id": "msg-0001",
                    "tool_calls": [],
                    "tool_call_id": None,
                },
                {
                    "type": "ai",
                    "content": "",
                    "id": "msg-0002",
                    "tool_calls": [
                        {
                            "name": "get_weather",
                            "args": {"city": "Chicago"},
                            "id": "tc-abc123",
                        }
                    ],
                    "tool_call_id": None,
                },
                {
                    "type": "tool",
                    "content": "72°F and sunny",
                    "id": "msg-0003",
                    "tool_calls": [],
                    "tool_call_id": "tc-abc123",
                },
            ],
        ),
        # step 3: AI gives final answer
        (
            "agent",
            [
                {
                    "type": "human",
                    "content": "What's the weather in Chicago?",
                    "id": "msg-0001",
                    "tool_calls": [],
                    "tool_call_id": None,
                },
                {
                    "type": "ai",
                    "content": "",
                    "id": "msg-0002",
                    "tool_calls": [
                        {
                            "name": "get_weather",
                            "args": {"city": "Chicago"},
                            "id": "tc-abc123",
                        }
                    ],
                    "tool_call_id": None,
                },
                {
                    "type": "tool",
                    "content": "72°F and sunny",
                    "id": "msg-0003",
                    "tool_calls": [],
                    "tool_call_id": "tc-abc123",
                },
                {
                    "type": "ai",
                    "content": "The weather in Chicago is 72°F and sunny.",
                    "id": "msg-0004",
                    "tool_calls": [],
                    "tool_call_id": None,
                },
            ],
        ),
        # step 4: final / end state
        (
            "__end__",
            [
                {
                    "type": "human",
                    "content": "What's the weather in Chicago?",
                    "id": "msg-0001",
                    "tool_calls": [],
                    "tool_call_id": None,
                },
                {
                    "type": "ai",
                    "content": "",
                    "id": "msg-0002",
                    "tool_calls": [
                        {
                            "name": "get_weather",
                            "args": {"city": "Chicago"},
                            "id": "tc-abc123",
                        }
                    ],
                    "tool_call_id": None,
                },
                {
                    "type": "tool",
                    "content": "72°F and sunny",
                    "id": "msg-0003",
                    "tool_calls": [],
                    "tool_call_id": "tc-abc123",
                },
                {
                    "type": "ai",
                    "content": "The weather in Chicago is 72°F and sunny.",
                    "id": "msg-0004",
                    "tool_calls": [],
                    "tool_call_id": None,
                },
            ],
        ),
    ]

    prev_id = None
    for i, (node, messages) in enumerate(steps):
        cp_id, cp_blob, meta_blob = make_checkpoint(i, node, messages)
        conn.execute(
            """
            INSERT INTO checkpoints
                (thread_id, checkpoint_id, parent_checkpoint_id, checkpoint, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (THREAD_ID, cp_id, prev_id, cp_blob, meta_blob),
        )
        prev_id = cp_id

    conn.commit()
    conn.close()
    print(f"Created {db_path} with 5 checkpoints for thread '{THREAD_ID}'")


if __name__ == "__main__":
    create_sample_session()
