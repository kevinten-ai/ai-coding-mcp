import asyncio
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class CLIResult:
    returncode: int
    stdout: str
    stderr: str
    execution_time: float
    error: Optional[str] = None

async def run_cli(
    command: list[str],
    cwd: Optional[str] = None,
    timeout: int = 30,
    env: Optional[dict] = None
) -> CLIResult:
    start_time = time.time()
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        execution_time = time.time() - start_time
        return CLIResult(
            returncode=proc.returncode,
            stdout=stdout.decode('utf-8', errors='replace'),
            stderr=stderr.decode('utf-8', errors='replace'),
            execution_time=execution_time
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return CLIResult(
            returncode=-1, stdout="", stderr="",
            execution_time=time.time() - start_time,
            error=f"Command timed out after {timeout}s"
        )
    except FileNotFoundError:
        return CLIResult(
            returncode=-1, stdout="", stderr="",
            execution_time=time.time() - start_time,
            error=f"Command not found: {command[0]}"
        )
    except Exception as e:
        return CLIResult(
            returncode=-1, stdout="", stderr="",
            execution_time=time.time() - start_time,
            error=str(e)
        )
