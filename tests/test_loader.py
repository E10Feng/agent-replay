"""Tests for CheckpointLoader."""

import pytest

from agent_replay.loader import CheckpointLoader


def test_loader_loads_checkpoints(sample_sqlite_db: str):
    """SQLite db with 5 checkpoints returns 5 items in step order."""
    loader = CheckpointLoader(db_url=f"sqlite:///{sample_sqlite_db}")
    checkpoints = loader.load_session("t1")

    assert len(checkpoints) == 5
    steps = [cp["step"] for cp in checkpoints]
    assert steps == sorted(steps), "checkpoints must be in step order"

    # Basic structure check
    for cp in checkpoints:
        assert "thread_id" in cp
        assert "checkpoint_id" in cp
        assert "step" in cp
        assert "node" in cp
        assert "state" in cp
        assert "metadata" in cp


def test_loader_empty_thread_raises(sample_sqlite_db: str):
    """load_session on an unknown thread_id raises ValueError."""
    loader = CheckpointLoader(db_url=f"sqlite:///{sample_sqlite_db}")
    with pytest.raises(ValueError, match="nonexistent"):
        loader.load_session("nonexistent")
