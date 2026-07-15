import pytest
import tempfile
import os
from tools.context.project_stats import _count_lines, get_project_stats

@pytest.mark.asyncio
async def test_project_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("# Comment\ndef hello():\n    return 'world'\n")
        with open(os.path.join(tmpdir, "app.js"), "w") as f:
            f.write("console.log('hello');")
        result = await get_project_stats(tmpdir)
        assert result["success"] is True
        assert result["data"]["total_files"] >= 2
        assert "python" in result["data"]["languages"]
        assert "javascript" in result["data"]["languages"]


def test_count_lines_returns_zero_for_file_errors(monkeypatch):
    def fail_open(*args, **kwargs):
        raise OSError("unreadable")

    monkeypatch.setattr("builtins.open", fail_open)
    assert _count_lines("unreadable.py") == 0


def test_count_lines_does_not_hide_programming_errors(monkeypatch):
    def fail_open(*args, **kwargs):
        raise RuntimeError("bug")

    monkeypatch.setattr("builtins.open", fail_open)
    with pytest.raises(RuntimeError, match="bug"):
        _count_lines("broken.py")
