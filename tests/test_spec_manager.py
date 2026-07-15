import pytest
import tempfile
import os
from pathlib import Path
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


@pytest.mark.asyncio
async def test_get_spec_rejects_path_outside_docs(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("private", encoding="utf-8")

    result = await get_spec(str(tmp_path), "docs/../secret.txt")

    assert result == {
        "success": False,
        "error": {
            "code": "INVALID_PATH",
            "message": "Spec path must stay within the project docs directory",
        },
    }


@pytest.mark.asyncio
async def test_create_spec_rejects_path_traversal_in_name(tmp_path: Path):
    result = await create_spec(str(tmp_path), "spec", "../escaped")

    assert result == {
        "success": False,
        "error": {
            "code": "INVALID_NAME",
            "message": "Invalid spec name: ../escaped",
        },
    }
    assert not (tmp_path / "docs" / "escaped.md").exists()


@pytest.mark.asyncio
async def test_get_spec_rejects_docs_symlink_outside_project(tmp_path: Path):
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (outside / "secret.md").write_text("private", encoding="utf-8")
    (project / "docs").symlink_to(outside, target_is_directory=True)

    result = await get_spec(str(project), "docs/secret.md")

    assert result["success"] is False
    assert result["error"]["code"] == "INVALID_PATH"


@pytest.mark.asyncio
async def test_create_spec_rejects_docs_symlink_outside_project(tmp_path: Path):
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / "docs").symlink_to(outside, target_is_directory=True)

    result = await create_spec(str(project), "spec", "escaped")

    assert result["success"] is False
    assert result["error"]["code"] == "INVALID_PATH"
    assert not any(outside.rglob("*.md"))
