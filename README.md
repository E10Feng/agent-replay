# AgentReplay

A CLI debugger for LangGraph agents. Step through past sessions checkpoint by
checkpoint — inspect messages, tool calls, and channel values at every node.
Think `git log` + `git diff`, but for your agent's reasoning process.

## Quick start

```bash
pip install -r requirements.txt
pip install -e .

# Generate a sample session
python examples/create_sample_session.py

# Start the interactive replay
agent-replay session --thread-id example-thread-001
```

## CLI options

```
agent-replay session --thread-id TEXT [--db-url TEXT] [--raw]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--thread-id` | (required) | Thread ID to load |
| `--db-url` | `sqlite:///checkpoints.sqlite` | SQLite path or PostgreSQL URL |
| `--raw` | off | Force raw SQLite access |

## REPL commands

| Command | Description |
|---------|-------------|
| `next` / `n` | Advance to next checkpoint |
| `back` / `b` | Go back to previous checkpoint |
| `jump N` | Jump to checkpoint N (1-indexed) |
| `inspect` | Show full state at current checkpoint |
| `diff` | Show diff vs previous checkpoint |
| `search QUERY` | Find checkpoints containing query |
| `list` | List all checkpoints |
| `help` | Show help |
| `quit` / `q` | Exit |
