import pytest
import tempfile
import os
from tools.specs.spec_manager import list_specs, get_spec, create_spec

@pytest.mark.asyncio
async def test_list_specs():
    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = os.path.join(tmpdir, "docs", "specs")
        os.makedirs(specs_dir)
        with open(os.path.join(specs_dir, "2026-01-01-test.md"), "w") as f:
            f.write("---\ntype: spec\ndate: 2026-01-01\nauthor: test\n---\n# Test Spec\nThis is a test.\n")
        result = await list_specs(tmpdir)
        assert result["success"] is True
        assert len(result["data"]["specs"]) == 1

@pytest.mark.asyncio
async def test_get_spec():
    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = os.path.join(tmpdir, "docs", "specs")
        os.makedirs(specs_dir)
        with open(os.path.join(specs_dir, "test.md"), "w") as f:
            f.write("# Test Spec\nContent here.")
        result = await get_spec(tmpdir, "docs/specs/test.md")
        assert result["success"] is True
        assert "Test Spec" in result["data"]["content"]

@pytest.mark.asyncio
async def test_create_spec():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await create_spec(tmpdir, "spec", "my-feature")
        assert result["success"] is True
        assert "path" in result["data"]
