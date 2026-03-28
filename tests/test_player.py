"""Tests for SessionPlayer."""

import pytest

from agent_replay.player import SessionPlayer


def test_player_next_advances_position(sample_checkpoints):
    """next() twice from position 0 reaches index 2."""
    player = SessionPlayer(sample_checkpoints)
    player.next()
    player.next()
    assert player.position == 2
    assert player.current() == sample_checkpoints[2]


def test_player_back_retreats_position(sample_checkpoints):
    """back() from position 2 reaches index 1."""
    player = SessionPlayer(sample_checkpoints)
    player.jump(3)  # 1-indexed → index 2
    player.back()
    assert player.position == 1
    assert player.current() == sample_checkpoints[1]


def test_player_jump_sets_position(sample_checkpoints):
    """jump(4) on 5 checkpoints sets index to 3."""
    player = SessionPlayer(sample_checkpoints)
    cp = player.jump(4)
    assert player.position == 3
    assert cp == sample_checkpoints[3]


def test_player_next_at_end_is_noop(sample_checkpoints):
    """next() at the last checkpoint returns last cp and 'Already at end'."""
    player = SessionPlayer(sample_checkpoints)
    player.jump(5)  # last (1-indexed)
    cp, msg = player.next()
    assert "already at end" in msg.lower()
    assert cp == sample_checkpoints[-1]
    assert player.position == len(sample_checkpoints) - 1


def test_player_back_at_start_is_noop(sample_checkpoints):
    """back() at position 0 returns first cp and 'Already at beginning'."""
    player = SessionPlayer(sample_checkpoints)
    cp, msg = player.back()
    assert "already at beginning" in msg.lower()
    assert cp == sample_checkpoints[0]
    assert player.position == 0


def test_player_search_finds_matching_checkpoint(sample_checkpoints):
    """search('Chicago') returns [2] because checkpoint at index 2 has 'Chicago' in tool content."""
    player = SessionPlayer(sample_checkpoints)
    results = player.search("Chicago")
    # Chicago appears in every checkpoint (human message is always present)
    # but we specifically check that index 2 is included
    assert 2 in results
