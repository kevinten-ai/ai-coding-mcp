import pytest
import tempfile
import os
from tools.specs.scaffold import scaffold_project

@pytest.mark.asyncio
async def test_scaffold_python_module():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await scaffold_project("python-module", tmpdir, {"name": "mymodule"})
        assert result["success"] is True
        assert os.path.exists(os.path.join(tmpdir, "mymodule", "__init__.py"))
        assert os.path.exists(os.path.join(tmpdir, "tests", "test_mymodule.py"))
