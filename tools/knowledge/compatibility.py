import json
from pathlib import Path
from utils.cli_runner import run_cli

async def _check_python_compatibility(project_path: str) -> dict:
    conflicts = []
    outdated = []
    result = await run_cli(["pip", "check"], cwd=project_path, timeout=30)
    if result.returncode != 0 and result.stdout:
        for line in result.stdout.strip().split('\n'):
            if line:
                conflicts.append(line)
    result = await run_cli(["pip", "list", "--outdated", "--format=json"], cwd=project_path, timeout=30)
    if result.returncode == 0:
        try:
            packages = json.loads(result.stdout)
            for pkg in packages:
                outdated.append({"name": pkg.get("name"), "current": pkg.get("version"), "latest": pkg.get("latest_version")})
        except json.JSONDecodeError:
            pass
    return {"conflicts": conflicts, "outdated": outdated}

async def check_compatibility(project_path: str) -> dict:
    try:
        root = Path(project_path)
        if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists():
            data = await _check_python_compatibility(project_path)
        elif (root / "package.json").exists():
            return {"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Node compatibility check not yet implemented"}}
        else:
            return {"success": False, "error": {"code": "UNKNOWN_ECOSYSTEM", "message": "Could not detect project ecosystem"}}
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}
