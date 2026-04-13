import pytest
from tools.knowledge.package_info import get_package_info

@pytest.mark.asyncio
async def test_get_package_info_python():
    result = await get_package_info("requests", "python")
    assert result["success"] is True
    assert "name" in result["data"]
    assert "version" in result["data"]
