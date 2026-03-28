"""Shared fixtures for AgentReplay tests."""

import json
import sqlite3
import tempfile
import uuid
from pathlib import Path

import pytest


def _make_checkpoint(step: int, node: str, messages: list[dict]) -> tuple[str, str]:
    """Return (checkpoint_json, metadata_json) for a synthetic checkpoint."""
    cp_id = str(uuid.uuid4())
    checkpoint = {
        "v": 1,
        "ts": f"2024-01-01T00:0{step}:00",
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
        "source": "loop" if step > 0 else "input",
        "writes": writes,
        "parents": {},
    }
    return json.dumps(checkpoint), json.dumps(metadata)


@pytest.fixture
def sample_checkpoints() -> list[dict]:
    """Five mock checkpoint dicts covering a weather-agent conversation."""
    msgs_by_step = [
        # step 0 — human question
        [{"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None}],
        # step 1 — AI tool call
        [
            {"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None},
            {"type": "ai", "content": "", "id": "m1", "tool_calls": [{"name": "get_weather", "args": {"city": "Chicago"}, "id": "tc1"}], "tool_call_id": None},
        ],
        # step 2 — tool result
        [
            {"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None},
            {"type": "ai", "content": "", "id": "m1", "tool_calls": [{"name": "get_weather", "args": {"city": "Chicago"}, "id": "tc1"}], "tool_call_id": None},
            {"type": "tool", "content": "72°F and sunny", "id": "m2", "tool_calls": [], "tool_call_id": "tc1"},
        ],
        # step 3 — AI final answer
        [
            {"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None},
            {"type": "ai", "content": "", "id": "m1", "tool_calls": [{"name": "get_weather", "args": {"city": "Chicago"}, "id": "tc1"}], "tool_call_id": None},
            {"type": "tool", "content": "72°F and sunny", "id": "m2", "tool_calls": [], "tool_call_id": "tc1"},
            {"type": "ai", "content": "The weather in Chicago is 72°F and sunny.", "id": "m3", "tool_calls": [], "tool_call_id": None},
        ],
        # step 4 — final state (same messages)
        [
            {"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None},
            {"type": "ai", "content": "", "id": "m1", "tool_calls": [{"name": "get_weather", "args": {"city": "Chicago"}, "id": "tc1"}], "tool_call_id": None},
            {"type": "tool", "content": "72°F and sunny", "id": "m2", "tool_calls": [], "tool_call_id": "tc1"},
            {"type": "ai", "content": "The weather in Chicago is 72°F and sunny.", "id": "m3", "tool_calls": [], "tool_call_id": None},
        ],
    ]
    nodes = ["__start__", "agent", "tools", "agent", "__end__"]

    cps = []
    for i, (messages, node) in enumerate(zip(msgs_by_step, nodes)):
        cp_blob, meta_blob = _make_checkpoint(i, node, messages)
        cp_data = json.loads(cp_blob)
        meta_data = json.loads(meta_blob)

        writes = meta_data.get("writes")
        node_name = list(writes.keys())[0] if writes else "unknown"

        cps.append(
            {
                "thread_id": "t1",
                "checkpoint_id": cp_data["id"],
                "step": i,
                "node": node_name,
                "state": {
                    "messages": messages,
                    "channel_values": cp_data["channel_values"],
                },
                "metadata": meta_data,
            }
        )
    return cps


@pytest.fixture
def sample_sqlite_db(tmp_path: Path) -> str:
    """Create a temporary SQLite file with 5 checkpoints for thread 't1'."""
    db_path = tmp_path / "checkpoints.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS checkpoints (
            thread_id TEXT,
            checkpoint_ns TEXT DEFAULT '',
            checkpoint_id TEXT,
            parent_checkpoint_id TEXT,
            type TEXT DEFAULT 'json',
            checkpoint BLOB,
            metadata BLOB
        )
        """
    )

    msgs_by_step = [
        [{"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None}],
        [
            {"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None},
            {"type": "ai", "content": "", "id": "m1", "tool_calls": [{"name": "get_weather", "args": {"city": "Chicago"}, "id": "tc1"}], "tool_call_id": None},
        ],
        [
            {"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None},
            {"type": "ai", "content": "", "id": "m1", "tool_calls": [{"name": "get_weather", "args": {"city": "Chicago"}, "id": "tc1"}], "tool_call_id": None},
            {"type": "tool", "content": "72°F and sunny", "id": "m2", "tool_calls": [], "tool_call_id": "tc1"},
        ],
        [
            {"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None},
            {"type": "ai", "content": "", "id": "m1", "tool_calls": [{"name": "get_weather", "args": {"city": "Chicago"}, "id": "tc1"}], "tool_call_id": None},
            {"type": "tool", "content": "72°F and sunny", "id": "m2", "tool_calls": [], "tool_call_id": "tc1"},
            {"type": "ai", "content": "The weather in Chicago is 72°F and sunny.", "id": "m3", "tool_calls": [], "tool_call_id": None},
        ],
        [
            {"type": "human", "content": "What's the weather in Chicago?", "id": "m0", "tool_calls": [], "tool_call_id": None},
            {"type": "ai", "content": "", "id": "m1", "tool_calls": [{"name": "get_weather", "args": {"city": "Chicago"}, "id": "tc1"}], "tool_call_id": None},
            {"type": "tool", "content": "72°F and sunny", "id": "m2", "tool_calls": [], "tool_call_id": "tc1"},
            {"type": "ai", "content": "The weather in Chicago is 72°F and sunny.", "id": "m3", "tool_calls": [], "tool_call_id": None},
        ],
    ]
    nodes = ["__start__", "agent", "tools", "agent", "__end__"]

    for i, (messages, node) in enumerate(zip(msgs_by_step, nodes)):
        cp_blob, meta_blob = _make_checkpoint(i, node, messages)
        cp_id = json.loads(cp_blob)["id"]
        conn.execute(
            "INSERT INTO checkpoints (thread_id, checkpoint_id, checkpoint, metadata) VALUES (?, ?, ?, ?)",
            ("t1", cp_id, cp_blob, meta_blob),
        )

    conn.commit()
    conn.close()
    return str(db_path)
