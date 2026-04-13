import pytest
import tempfile
import os
from tools.context.dependency_graph import get_dependency_graph

@pytest.mark.asyncio
async def test_dependency_graph():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("import os\nfrom utils import helper\nimport external_lib\n")
        os.makedirs(os.path.join(tmpdir, "utils"), exist_ok=True)
        with open(os.path.join(tmpdir, "utils", "__init__.py"), "w") as f:
            f.write("def helper(): pass")
        result = await get_dependency_graph(tmpdir, "main.py")
        assert result["success"] is True
        assert "dependencies" in result["data"]
