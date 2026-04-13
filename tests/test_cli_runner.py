import pytest
from utils.cli_runner import run_cli, CLIResult

@pytest.mark.asyncio
async def test_run_cli_success():
    result = await run_cli(["echo", "hello"])
    assert result.returncode == 0
    assert "hello" in result.stdout

@pytest.mark.asyncio
async def test_run_cli_timeout():
    result = await run_cli(["sleep", "10"], timeout=0.1)
    assert result.returncode != 0
    assert "timed out" in result.error.lower()
