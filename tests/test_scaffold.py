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


@pytest.mark.asyncio
async def test_scaffold_rejects_path_traversal_in_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = os.path.join(tmpdir, "target")
        result = await scaffold_project("python-module", target, {"name": "../escaped"})

        assert result == {
            "success": False,
            "error": {
                "code": "INVALID_PARAM",
                "message": "Invalid project name: ../escaped",
            },
        }
        assert not os.path.exists(os.path.join(tmpdir, "escaped"))
