import pytest
import tempfile
import os
from tools.knowledge.compatibility import check_compatibility

@pytest.mark.asyncio
async def test_check_compatibility_python():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
            f.write("requests>=2.0.0\n")
        result = await check_compatibility(tmpdir)
        assert result["success"] is True
        assert "conflicts" in result["data"]
