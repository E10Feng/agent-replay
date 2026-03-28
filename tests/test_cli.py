"""Tests for the Click CLI."""

from click.testing import CliRunner

from agent_replay.cli import cli


def test_cli_session_command_exits_cleanly(sample_sqlite_db: str):
    """CliRunner with 'quit\\n' input exits with code 0."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "session",
            "--thread-id", "t1",
            "--db-url", f"sqlite:///{sample_sqlite_db}",
        ],
        input="quit\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0, (
        f"Expected exit code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    )
