import pytest
import tempfile
import os
import subprocess
from tools.workflow.git_ops import git_status, git_history

@pytest.mark.asyncio
async def test_git_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)
        with open(os.path.join(tmpdir, "test.txt"), "w") as f:
            f.write("hello")
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)
        result = await git_status(tmpdir)
        assert result["success"] is True
        assert "branch" in result["data"]

@pytest.mark.asyncio
async def test_git_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)
        with open(os.path.join(tmpdir, "test.txt"), "w") as f:
            f.write("hello")
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)
        result = await git_history(tmpdir)
        assert result["success"] is True
        assert len(result["data"]["commits"]) >= 1
