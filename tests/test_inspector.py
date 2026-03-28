"""Tests for StateInspector."""

import pytest

from agent_replay.inspector import StateInspector


def _make_cp(step: int, messages: list[dict]) -> dict:
    return {
        "thread_id": "t1",
        "checkpoint_id": f"cp-{step}",
        "step": step,
        "node": "agent",
        "state": {
            "messages": messages,
            "channel_values": {"messages": messages},
        },
        "metadata": {"step": step},
    }


def test_inspector_formats_human_message():
    """format_state with a HumanMessage returns a string containing the message content."""
    inspector = StateInspector()
    cp = _make_cp(
        0,
        [{"type": "human", "content": "What's the weather?", "id": "m0", "tool_calls": [], "tool_call_id": None}],
    )
    output = inspector.format_state(cp)
    assert "What's the weather?" in output


def test_inspector_formats_tool_call():
    """format_state with an AIMessage with tool_call contains tool name and arg."""
    inspector = StateInspector()
    cp = _make_cp(
        1,
        [
            {
                "type": "ai",
                "content": "",
                "id": "m1",
                "tool_calls": [{"name": "get_weather", "args": {"city": "Chicago"}, "id": "tc1"}],
                "tool_call_id": None,
            }
        ],
    )
    output = inspector.format_state(cp)
    assert "get_weather" in output
    assert "Chicago" in output


def test_inspector_diff_shows_new_message():
    """diff(cp1, cp2) where cp2 adds a message shows a '+' marker."""
    inspector = StateInspector()
    cp1 = _make_cp(
        0,
        [{"type": "human", "content": "Hello", "id": "m0", "tool_calls": [], "tool_call_id": None}],
    )
    cp2 = _make_cp(
        1,
        [
            {"type": "human", "content": "Hello", "id": "m0", "tool_calls": [], "tool_call_id": None},
            {"type": "ai", "content": "Hi there!", "id": "m1", "tool_calls": [], "tool_call_id": None},
        ],
    )
    diff_output = inspector.diff(cp1, cp2)
    assert "+" in diff_output
