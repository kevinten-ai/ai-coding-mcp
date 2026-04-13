import pytest
import tempfile
import os
from tools.context.code_indexer import index_project, get_symbol_info

@pytest.mark.asyncio
async def test_index_project_python():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "test.py"), "w") as f:
            f.write('def hello():\n    return "world"\n\nclass MyClass:\n    def method(self):\n        pass\n')
        result = await index_project(tmpdir, language="python")
        assert result["success"] is True
        assert "symbols" in result["data"]
        assert len(result["data"]["symbols"]) >= 2

@pytest.mark.asyncio
async def test_get_symbol_info():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "test.py"), "w") as f:
            f.write("def hello(): return 'world'")
        await index_project(tmpdir)
        result = await get_symbol_info(tmpdir, "hello")
        assert result["success"] is True
        assert result["data"]["name"] == "hello"
