# AgentReplay — Build Spec

## Overview
AgentReplay is a CLI debugger for LangGraph agents that lets you step through past sessions checkpoint by checkpoint. It reads from a RecallGraph (LangGraph checkpoint backend) and lets you inspect the full agent state — messages, tool calls, channel values — at every node. Think `git log` + `git diff`, but for your agent's reasoning process.

**Who it's for:** Developers building LangGraph-powered agents who need to debug failed runs, understand decision branches, or audit what their agent actually did.

**Pain it solves:** Agent runs are black boxes. When something goes wrong, you have no way to replay and inspect the state transitions that led to a bad outcome. AgentReplay turns every past session into an interactive debugger session.

## Architecture

```
CLI Entry (agent_replay/cli.py)
    │
    ├── CheckpointLoader (agent_replay/loader.py)
    │       └── Connects to RecallGraph/LangGraph checkpoint store
    │           Fetches checkpoints by thread_id, ordered by step
    │
    ├── SessionPlayer (agent_replay/player.py)
    │       └── Manages current position in the checkpoint sequence
    │           Exposes step(), back(), jump(n) methods
    │           Tracks current checkpoint index
    │
    ├── StateInspector (agent_replay/inspector.py)
    │       └── Formats checkpoint state for display
    │           Handles messages, tool_calls, channel values
    │           Produces diff between two consecutive checkpoints
    │
    └── UI (agent_replay/ui.py)
            └── Rich-powered terminal UI
                Interactive REPL: next/back/jump/inspect/diff/search/quit
                Keyboard-friendly command interface
```

**Data flow:**
1. User provides `--thread-id` (and optionally `--db-url`)
2. Loader fetches all checkpoints for that thread from the LangGraph checkpoint SQLite/Postgres store
3. Player wraps the checkpoint list and tracks position
4. UI renders current state using Rich, accepts commands to navigate

## Tech Stack

- **Python 3.11+**
- **langgraph** — for checkpoint schema compatibility and `SqliteSaver`/`PostgresSaver`
- **langchain-core** — message types
- **rich** — terminal UI (panels, tables, syntax highlighting, diffs)
- **click** — CLI commands and flags
- **sqlite3** — built-in, default checkpoint backend (SQLite)
- **psycopg2-binary** — optional, for PostgreSQL checkpoint backend
- **pytest** — test runner
- **pytest-mock** — mocking for unit tests

Pinned versions in requirements.txt:
```
langgraph>=0.2.0
langchain-core>=0.3.0
rich>=13.7.0
click>=8.1.7
psycopg2-binary>=2.9.9
pytest>=8.0.0
pytest-mock>=3.12.0
```

## File Structure

```
agent-replay/
├── BUILD-SPEC.md
├── README.md
├── .gitignore
├── requirements.txt
├── setup.py
├── agent_replay/
│   ├── __init__.py
│   ├── cli.py           # Click CLI entry point: `agent-replay` command
│   ├── loader.py        # CheckpointLoader: fetch checkpoints from store
│   ├── player.py        # SessionPlayer: navigate checkpoint sequence
│   ├── inspector.py     # StateInspector: format/diff checkpoint state
│   └── ui.py            # Rich-powered interactive REPL
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Fixtures: mock checkpoint data, SQLite db
│   ├── test_loader.py
│   ├── test_player.py
│   ├── test_inspector.py
│   └── test_cli.py
└── examples/
    ├── create_sample_session.py   # Script to generate a sample LangGraph session for demo
    └── README.md
```

## Core Features (MVP scope only)

1. **Load session by thread_id** — Connect to a LangGraph SQLite checkpoint file (default: `checkpoints.sqlite`) or Postgres URL via `--db-url`. Fetch all checkpoints for a given `--thread-id`, ordered by step number.

2. **Interactive step navigation** — REPL-style interface with commands: `next` (or `n`), `back` (or `b`), `jump <N>`, `quit` (or `q`). Shows current position (e.g., "Step 3 of 7") and node name at each checkpoint.

3. **Full state inspection** — At any checkpoint, display the full state: all messages (human/AI/tool), tool call requests and results, and any custom channel values. Rendered with Rich panels and syntax highlighting.

4. **Checkpoint diff** — `diff` command shows what changed between the current checkpoint and the previous one. Highlights added/removed/changed fields in messages and channel values.

5. **Search across checkpoints** — `search <query>` scans all checkpoints in the session and returns step numbers where the query string appears (in message content, tool names, or channel values). Jump directly to a result.

## Implementation Notes

- **Checkpoint schema:** LangGraph stores checkpoints in a SQLite table `checkpoints` with columns: `thread_id`, `checkpoint_ns`, `checkpoint_id`, `parent_checkpoint_id`, `type`, `checkpoint` (blob), `metadata` (blob). The `checkpoint` blob is msgpack or JSON-serialized. Use `langgraph`'s `BaseCheckpointSaver` / `get_tuple` method to deserialize properly rather than raw SQL where possible.

- **Fallback to raw SQL:** If the LangGraph API for reading checkpoints isn't stable across versions, fall back to reading the SQLite file directly with `sqlite3` and deserializing the blob with `pickle`/`json`. Add a `--raw` flag to force this mode.

- **No live agent required:** AgentReplay only reads from the checkpoint store — it never runs the graph. This makes it safe to use on production checkpoint files.

- **Thread safety:** Read-only access, single-threaded CLI — no concurrency concerns.

- **Rich layout:** Use `rich.live` or `rich.console` with panels. Don't use a full TUI framework (textual) — keep it simple with a print-then-prompt loop.

- **Message rendering:** LangGraph messages follow LangChain's `BaseMessage` schema. Detect type by `type` field: `human`, `ai`, `tool`. For `ai` messages with `tool_calls`, show each tool call as a separate sub-panel.

- **Edge case — empty sessions:** If a thread_id has no checkpoints, print a clear error and exit with code 1.

- **Edge case — single checkpoint:** Navigation commands should gracefully handle being at the first or last checkpoint (print "Already at beginning" / "Already at end").

## API / Interface

### CLI Commands

```bash
# Basic usage — interactive REPL
agent-replay session --thread-id <THREAD_ID> [--db-url <URL>]

# Options:
#   --thread-id TEXT   Thread ID to load (required)
#   --db-url TEXT      SQLite path or PostgreSQL URL
#                      Default: sqlite:///checkpoints.sqlite
#   --raw              Use raw SQLite access instead of LangGraph API

# Interactive REPL commands (once inside a session):
#   next | n           Advance to next checkpoint
#   back | b           Go back to previous checkpoint
#   jump <N>           Jump to checkpoint number N (1-indexed)
#   inspect            Show full state at current checkpoint (default view)
#   diff               Show diff vs previous checkpoint
#   search <query>     Find checkpoints containing query string
#   list               Show all checkpoints with step numbers and node names
#   help               Show available commands
#   quit | q           Exit
```

### Programmatic API (for test use)

```python
from agent_replay.loader import CheckpointLoader
from agent_replay.player import SessionPlayer
from agent_replay.inspector import StateInspector

loader = CheckpointLoader(db_url="sqlite:///checkpoints.sqlite")
checkpoints = loader.load_session(thread_id="my-thread")
player = SessionPlayer(checkpoints)
inspector = StateInspector()

# Navigate
cp = player.current()
player.next()
player.back()
player.jump(3)

# Inspect
state_str = inspector.format_state(player.current())
diff_str = inspector.diff(player.previous(), player.current())
results = player.search("weather tool")
```

## Setup & Run

```bash
# Clone and set up
cd agent-replay
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
pip install -e .

# Generate a sample session to play with
python examples/create_sample_session.py
# Creates checkpoints.sqlite in current directory

# Run the debugger
agent-replay session --thread-id example-thread-001

# Or point at a specific db
agent-replay session --thread-id my-thread --db-url sqlite:///path/to/checkpoints.sqlite
```

## Test Cases

### Happy Path

1. `test_loader_loads_checkpoints` — Given a SQLite file with 5 checkpoints for thread `t1`, `CheckpointLoader.load_session("t1")` returns a list of 5 checkpoint objects in step order.

2. `test_player_next_advances_position` — Given a `SessionPlayer` with 3 checkpoints, calling `next()` twice moves position from 0 to 2; `current()` returns the checkpoint at index 2.

3. `test_player_back_retreats_position` — Given a `SessionPlayer` at position 2, calling `back()` moves to position 1; `current()` returns checkpoint at index 1.

4. `test_player_jump_sets_position` — Given a `SessionPlayer` with 5 checkpoints, `jump(4)` (1-indexed) sets position to index 3; `current()` returns checkpoint 4.

5. `test_inspector_formats_human_message` — Given a checkpoint state with a `HumanMessage("What's the weather?")`, `StateInspector.format_state()` returns a string containing "What's the weather?".

6. `test_inspector_formats_tool_call` — Given a checkpoint with an `AIMessage` containing a tool call `{name: "get_weather", args: {city: "Chicago"}}`, `format_state()` output contains "get_weather" and "Chicago".

7. `test_inspector_diff_shows_new_message` — Given two consecutive checkpoints where the second adds one new `AIMessage`, `inspector.diff(cp1, cp2)` output contains a marker indicating the new message was added.

8. `test_player_search_finds_matching_checkpoint` — Given a session with 4 checkpoints where checkpoint 3 contains the text "Chicago", `player.search("Chicago")` returns `[2]` (0-indexed) or equivalent step indicator.

9. `test_cli_session_command_exits_cleanly` — Invoking `agent-replay session --thread-id example-thread-001` against the sample SQLite db (created by `create_sample_session.py`) launches the REPL without error (exit code 0 after `quit`). Use Click's `CliRunner` with simulated `quit` input.

### Edge Cases

10. `test_loader_empty_thread_raises` — `CheckpointLoader.load_session("nonexistent-thread")` on a valid SQLite file raises `ValueError` or returns an empty list, and the CLI prints an error message and exits with code 1.

11. `test_player_next_at_end_is_noop` — At the last checkpoint, calling `next()` does not raise an exception; `current()` still returns the last checkpoint; player returns a message like "Already at end".

12. `test_player_back_at_start_is_noop` — At checkpoint 0, calling `back()` does not raise an exception; `current()` still returns checkpoint 0; player returns a message like "Already at beginning".
