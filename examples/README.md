# Examples

## create_sample_session.py

Generates a `checkpoints.sqlite` file in the current working directory with a
5-step weather-agent conversation under thread_id `example-thread-001`.

```bash
cd agent-replay
python examples/create_sample_session.py
```

Then start the interactive replay:

```bash
agent-replay session --thread-id example-thread-001
```

Use `help` inside the REPL to see all available commands.
