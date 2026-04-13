import json
from utils.cli_runner import run_cli
from utils.cache import FileCache
from config import config

async def _get_pypi_info(package_name: str) -> dict:
    result = await run_cli(["pip", "index", "versions", package_name], timeout=10)
    if result.returncode != 0:
        api_result = await run_cli(["curl", "-s", f"https://pypi.org/pypi/{package_name}/json"], timeout=10)
        if api_result.returncode == 0:
            try:
                data = json.loads(api_result.stdout)
                return {"name": data["info"]["name"], "version": data["info"]["version"],
                        "latest_version": data["info"]["version"], "description": data["info"]["summary"],
                        "license": data["info"]["license"], "homepage": data["info"]["home_page"]}
            except (json.JSONDecodeError, KeyError):
                pass
    return {"name": package_name, "version": "unknown"}

async def _get_npm_info(package_name: str) -> dict:
    result = await run_cli(["npm", "view", package_name, "--json"], timeout=10)
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return {"name": data.get("name"), "version": data.get("version"),
                    "latest_version": data.get("dist-tags", {}).get("latest"),
                    "description": data.get("description"), "license": data.get("license"),
                    "homepage": data.get("homepage")}
        except json.JSONDecodeError:
            pass
    return {"name": package_name, "version": "unknown"}

async def get_package_info(package_name: str, ecosystem: str) -> dict:
    try:
        cache = FileCache(f"{config.cache.cache_dir}/packages", ttl=3600)
        cache_key = f"{ecosystem}:{package_name}"
        cached = cache.get(cache_key)
        if cached:
            return {"success": True, "data": cached}
        if ecosystem == "python":
            data = await _get_pypi_info(package_name)
        elif ecosystem == "node":
            data = await _get_npm_info(package_name)
        else:
            return {"success": False, "error": {"code": "UNSUPPORTED_ECOSYSTEM", "message": f"Ecosystem '{ecosystem}' not yet supported"}}
        cache.set(cache_key, data)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}
